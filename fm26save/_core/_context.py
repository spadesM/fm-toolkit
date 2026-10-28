"""Per-save state that readers share: decompressed sections on loan, and cached results.

A reader borrows a section's bytes with `section(name)`. Nested borrows of the same
section share one decompressed bytes object, which is dropped when the outermost borrow
ends, so a whole section is never kept alive between reader calls. Results that are
cheap to keep (tables and small indexes) go in the cache through `cached(key, build)`,
which also remembers a pass that failed so nothing pays to decode it twice. Closing the
context drops both; values already handed out keep working.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import AbstractContextManager, contextmanager
from types import MemberDescriptorType
from typing import cast

from fm26save._core._container import (
    ContainerIndex,
    DirectoryEntry,
    match_file_entries,
    read_directory_entry,
    read_region_frames,
    read_section,
)
from fm26save._core._errors import FmsaveError, SaveClosedError
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import NamePoolLayout, PlayerRecordLayout, find_layout
from fm26save._core.models.meta import SaveInfo
from fm26save._core.name_maps import _EMPTY_COMPETITION_NAMES  # pyright: ignore[reportPrivateUsage]
from fm26save._core.readers._common import GAME_DB_SECTION, SPAN_REGION
from fm26save._core.readers.clubs import (
    ClubIndex,
    ClubRecordSpan,
    find_club_layouts,
    own_record_spans,
    read_club_index,
)
from fm26save._core.readers.competitions import (
    CompetitionIndex,
    build_competition_index,
    find_competition_id_pair_layout,
    locate_competition_database_ids,
)
from fm26save._core.readers.names import NAME_POOLS_CACHE_KEY, NamePools, locate_name_pools
from fm26save._core.readers.player_scan import (
    PLAYER_RECORDS_CACHE_KEY,
    PlayerRecords,
    locate_player_records,
)
from fm26save._core.readers.span import (
    SPAN_RECORDS_CACHE_KEY,
    SpanRecords,
    find_span_layouts,
    missing_clock_error,
    scan_span,
)
from fm26save._core.readers.stadiums import StadiumIndex, find_stadium_layout, read_stadium_index
from fm26save._core.readers.stages import StageIndex, find_stage_layout, read_stage_index

CLUB_INDEX_CACHE_KEY = "club_index"
OWN_CLUB_RECORD_SPANS_CACHE_KEY = "own_club_record_spans"
STAGE_INDEX_CACHE_KEY = "stage_index"
COMPETITION_INDEX_CACHE_KEY = "competition_index"
STADIUM_INDEX_CACHE_KEY = "stadium_index"


def closed_save_error() -> SaveClosedError:
    return SaveClosedError("this save is closed; open it again with fmsave.open()")


def _detached_error(error: FmsaveError) -> FmsaveError:
    """Copy exception state without invoking its constructor or retaining exception chains."""
    detached = BaseException.__new__(type(error))
    detached.args = error.args
    detached.__dict__.update(error.__dict__)
    # Structured subclasses can keep fields in slots as well as their instance dictionary.
    for owner in type(error).__mro__:
        for descriptor in vars(owner).values():
            if isinstance(descriptor, MemberDescriptorType):
                try:
                    value = descriptor.__get__(error, type(error))
                except AttributeError:
                    continue
                descriptor.__set__(detached, value)
    if hasattr(error, "__notes__"):
        detached.__notes__ = error.__notes__.copy()
    return detached


class _FailedBuild:
    """A remembered failure: the error a cached build raised, kept under that build's key."""

    __slots__ = ("error",)

    def __init__(self, error: FmsaveError) -> None:
        self.error = _detached_error(error)


class SaveContext:
    """Section loans and a result cache for one open save. Not thread-safe."""

    __slots__ = (
        "_cache",
        "_closed",
        "_competition_names",
        "_container_index",
        "_info",
        "_loan_counts",
        "_loaned_sections",
    )

    def __init__(
        self,
        container_index: ContainerIndex,
        info: SaveInfo,
        *,
        competition_names: FrozenMapping[int, str] = _EMPTY_COMPETITION_NAMES,
    ) -> None:
        self._container_index = container_index
        self._info = info
        self._competition_names = competition_names
        self._closed = False
        self._cache: dict[str, object] = {}
        self._loaned_sections: dict[str, bytes] = {}
        self._loan_counts: dict[str, int] = {}

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def info(self) -> SaveInfo:
        return self._info

    @property
    def competition_names(self) -> FrozenMapping[int, str]:
        """The names the save was opened with, keyed on the editor database id.

        Empty unless a name map was passed to `fmsave.open`, because no save stores a
        competition name. It is fixed for the life of the save: tables are cached, so a
        different map means opening the save again.
        """
        return self._competition_names

    def section(self, name: str) -> AbstractContextManager[bytes]:
        """Borrow the decompressed bytes of section `name` for the length of a `with` block.

        Raises:
            SaveClosedError: The context is closed.
        """
        self._require_open()
        return self._section_loan(name)

    def cached[ValueT](self, key: str, build: Callable[[], ValueT]) -> ValueT:
        """Return the value stored under `key`, building and storing it on first use.

        A build that raises the library's own error is remembered as having failed, and
        every later call for that key raises it again without rebuilding. A pass reads the
        same immutable bytes every time, so a second attempt would fail the same way after
        paying the same cost: on a save whose player pass fails, one `validate_save` run
        used to decode that pass six times. Any other exception stores nothing, because it
        says something about the machine rather than about the save. Never store section
        bytes here.

        A failed reader check is remembered on the same terms, and only a save opened with
        `strict=True` raises one at all. That rests on `Save` settling its strictness when the
        save is opened and never changing it: a failure remembered under one setting and met
        under another would be a remembered answer to a question nobody asked again.

        Raises:
            SaveClosedError: The context is closed.
        """
        self._require_open()
        if key in self._cache:
            stored = self._cache[key]
            if isinstance(stored, _FailedBuild):
                raise _detached_error(stored.error)
            return cast("ValueT", stored)
        try:
            value = build()
        except FmsaveError as error:
            if not self._closed:
                self._cache[key] = _FailedBuild(error)
            raise
        if not self._closed:
            self._cache[key] = value
        return value

    def cached_value(self, key: str) -> object | None:
        """Return the value stored under `key`, or None when nothing is stored.

        A key whose build failed counts as nothing stored: callers ask this to find out
        whether a value is ready to hand, and a remembered failure is not one.

        Raises:
            SaveClosedError: The context is closed.
        """
        self._require_open()
        stored = self._cache.get(key)
        return None if isinstance(stored, _FailedBuild) else stored

    def club_index(self) -> ClubIndex:
        """Every club with the team to club map, read from `game_db` once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: No club record is accepted, a club uid or club index appears
                in two records, or a team id is listed twice (by one club or by two).
        """
        return self.cached(CLUB_INDEX_CACHE_KEY, self._build_club_index)

    def _build_club_index(self) -> ClubIndex:
        save_info = self._info
        layouts = find_club_layouts(save_info.section_schemas.get(GAME_DB_SECTION), save_info.build)
        with self.section(GAME_DB_SECTION) as game_db:
            return read_club_index(game_db, layouts, save_info.file_name)

    def own_club_record_spans(self) -> tuple[ClubRecordSpan, ...]:
        """The club index's record spans cut short at records the club scan did not accept,
        found once and then cached, for the readers that search a club's own data.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: As for `club_index`.
        """
        return self.cached(OWN_CLUB_RECORD_SPANS_CACHE_KEY, self._build_own_club_record_spans)

    def _build_own_club_record_spans(self) -> tuple[ClubRecordSpan, ...]:
        save_info = self._info
        layouts = find_club_layouts(save_info.section_schemas.get(GAME_DB_SECTION), save_info.build)
        club_index = self.club_index()
        with self.section(GAME_DB_SECTION) as game_db:
            return own_record_spans(game_db, club_index, layouts.records)

    def name_pools(self) -> NamePools:
        """The three name pools, read from `game_db` once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: The signature is missing or appears more than once, an entry id
                differs from its index, a name is longer than the layout allows, or (on a
                full-size `game_db`) a pool has fewer entries than the layout requires.
            CorruptSaveError: A pool runs past the end of `game_db`.
        """
        return self.cached(NAME_POOLS_CACHE_KEY, self._build_name_pools)

    def _build_name_pools(self) -> NamePools:
        save_info = self._info
        layout = find_layout(
            NamePoolLayout,
            GAME_DB_SECTION,
            save_info.section_schemas.get(GAME_DB_SECTION),
            save_info.build,
        ).layout
        with self.section(GAME_DB_SECTION) as game_db:
            return locate_name_pools(game_db, layout, save_info.file_name)

    def player_records(self) -> PlayerRecords:
        """Every accepted player record's offset, pindex and uid, read once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: No player records were found, a pindex or uid appears in two
                records, or the name pools cannot be located.
            CorruptSaveError: A player record runs past the end of `game_db`.
        """
        return self.cached(PLAYER_RECORDS_CACHE_KEY, self._build_player_records)

    def _build_player_records(self) -> PlayerRecords:
        save_info = self._info
        layout = find_layout(
            PlayerRecordLayout,
            GAME_DB_SECTION,
            save_info.section_schemas.get(GAME_DB_SECTION),
            save_info.build,
        ).layout
        with self.section(GAME_DB_SECTION) as game_db:
            # name_pools() is called inside this borrow so its own internal borrow shares
            # this one, instead of decompressing game_db a second time on a cold call.
            name_pools = self.name_pools()
            return locate_player_records(
                game_db, name_pools.end_offset, layout, save_info.file_name
            )

    def span_records(self) -> SpanRecords:
        """Fixtures, league-table blocks and rules preambles from one streamed pass over the
        unnamed span, read once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            CorruptSaveError: The span is damaged or was being written.
            ReaderCheckError: The save's in-game date is unreadable, so the fixture year
                window cannot be built.
        """
        return self.cached(SPAN_RECORDS_CACHE_KEY, self._build_span_records)

    def _build_span_records(self) -> SpanRecords:
        save_info = self._info
        clock = save_info.game_date
        if clock is None:
            raise missing_clock_error(save_info.file_name)
        # The span is a run of unlisted frames, not a section: it is streamed one frame at a
        # time through read_region_frames, and never borrowed whole through section().
        frames = read_region_frames(self._container_index, SPAN_REGION)
        return scan_span(frames, find_span_layouts(save_info.build), clock, save_info.file_name)

    def stage_index(self) -> StageIndex:
        """Every stage row with the competition joins, read from `game_db` once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: No stage table was found in the tail of `game_db`, or a stage id
                appears in two rows.
        """
        return self.cached(STAGE_INDEX_CACHE_KEY, self._build_stage_index)

    def _build_stage_index(self) -> StageIndex:
        save_info = self._info
        layout = find_stage_layout(save_info.section_schemas.get(GAME_DB_SECTION), save_info.build)
        with self.section(GAME_DB_SECTION) as game_db:
            return read_stage_index(game_db, layout, save_info.file_name)

    def stadium_index(self) -> StadiumIndex:
        """Every stadium row with the ordinal lookup, read from `game_db` once and then cached.

        The index is private: the fixture reader joins through it and the stadium reader builds
        its rows from it, and neither hands out an ordinal.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: No stadium table head was accepted, or a stadium uid appears in
                two rows.
        """
        return self.cached(STADIUM_INDEX_CACHE_KEY, self._build_stadium_index)

    def _build_stadium_index(self) -> StadiumIndex:
        save_info = self._info
        layout = find_stadium_layout(
            save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
        )
        with self.section(GAME_DB_SECTION) as game_db:
            return read_stadium_index(game_db, layout, save_info.file_name)

    def competition_index(self) -> CompetitionIndex:
        """Every competition with its database id and, when the user supplied a name map, its
        name. Read from `game_db` once and then cached.

        Raises:
            SaveClosedError: The context is closed.
            ReaderCheckError: No stage table was found in the tail of `game_db`, or a stage id
                appears in two rows.
        """
        return self.cached(COMPETITION_INDEX_CACHE_KEY, self._build_competition_index)

    def _build_competition_index(self) -> CompetitionIndex:
        save_info = self._info
        layout = find_competition_id_pair_layout(
            save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
        )
        with self.section(GAME_DB_SECTION) as game_db:
            # stage_index() is called inside this borrow so its own borrow shares these bytes,
            # and the id-pair records are read from the very same ones, so a cold call
            # decompresses game_db once for both rather than once each.
            stage_index = self.stage_index()
            database_ids = locate_competition_database_ids(game_db, layout)
        return build_competition_index(stage_index, database_ids, self._competition_names)

    def match_file_entries(self) -> tuple[DirectoryEntry, ...]:
        """The save's per-match directory entries, in directory order.

        Nothing is read from the file here: the entries come from the directory the save was
        opened with. A save may list none at all.

        Raises:
            SaveClosedError: The context is closed.
        """
        self._require_open()
        return match_file_entries(self._container_index)

    def read_match_file(self, entry: DirectoryEntry) -> bytes:
        """The decompressed bytes of one per-match entry. Nothing is cached or held.

        Raises:
            SaveClosedError: The context is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The entry is damaged or was being written.
        """
        self._require_open()
        return read_directory_entry(self._container_index, entry)

    def close(self) -> None:
        """Drop cached values and section loans. Calling it again does nothing."""
        self._closed = True
        self._cache.clear()
        self._loaned_sections.clear()
        self._loan_counts.clear()

    def __repr__(self) -> str:
        state = "closed" if self._closed else "open"
        values = sum(not isinstance(stored, _FailedBuild) for stored in self._cache.values())
        failures = len(self._cache) - values
        failed = f", {failures} failed" if failures else ""
        return f"<fmsave SaveContext {state}, {values} cached{failed}>"

    def _require_open(self) -> None:
        if self._closed:
            raise closed_save_error()

    @contextmanager
    def _section_loan(self, name: str) -> Generator[bytes]:
        self._require_open()
        section_bytes = self._loaned_sections.get(name)
        if section_bytes is None:
            section_bytes = read_section(self._container_index, name)
            self._loaned_sections[name] = section_bytes
        self._loan_counts[name] = self._loan_counts.get(name, 0) + 1
        try:
            yield section_bytes
        finally:
            self._end_loan(name)

    def _end_loan(self, name: str) -> None:
        remaining_loans = self._loan_counts.get(name, 0) - 1
        if remaining_loans > 0:
            self._loan_counts[name] = remaining_loans
            return
        self._loan_counts.pop(name, None)
        self._loaned_sections.pop(name, None)
