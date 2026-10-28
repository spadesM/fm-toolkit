"""The stadium table in `game_db`, and the calendar link that says who plays where.

The table is a run of rows whose first field is the row's own place in it, counting from one.
That is what makes it findable: a pattern matching the words 1, 2 and 3 one row apart is
common enough to hit dozens of places in a section this size, so a hit counts only when a
dozen rows from there each store their own ordinal with the stadium uid written twice and a
zero byte after it. One candidate survived that on every save measured, and the head sits at no
fixed fraction of the section, so nothing here is a fixed offset.

The walk then steps row by row and stops at the first row that is not the next one. It never
resynchronises, deliberately: a walk that skipped over bytes it could not read would turn a
layout that had moved into a shorter, quietly wrong table instead of a visibly empty one. Two
row shapes exist, and one flag bit tells them apart: a row that carries its name inline is
longer by the name and the word holding its length.

The ordinal itself is never exposed. It is a position in a table, not an id the game shows,
and a save that added a row would renumber everything after it. What leaves this module is the
uid, which is the stored value plus one, the same convention club uids follow.

**No club record points at a ground.** The link this module builds instead is a vote over the
fixture calendar: the ground a club played most of its first-team home matches at is its home
ground, once the calendar records enough of them. Ownership is a separate, stored field, and
the two disagree for about three grounds in ten.
"""

from __future__ import annotations

import datetime
import functools
import re
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import StadiumTableLayout, find_layout
from fm26save._core._reader_stats import StadiumStats
from fm26save._core._scan import decode_date
from fm26save._core.models.clubs import Club
from fm26save._core.models.fixtures import Fixture
from fm26save._core.models.stadiums import Stadium
from fm26save._core.readers._common import (
    GAME_DB_SECTION,
    MISSING_REFERENCE,
    build_gap_padded_struct,
    layout_mismatch,
)
from fm26save._core.readers.clubs import ClubIndex

# The first team of a club is the one whose home matches decide that club's home ground; a
# reserve or youth side often plays somewhere else entirely.
_FIRST_TEAM_SLOT = 0
_DATE_BYTES = 4
# One little-endian u32, which reads the third date as one int and a named row's name length.
_WORD = struct.Struct("<I")


@dataclass(frozen=True, slots=True)
class RawStadium:
    """One row of the stadium table, decoded but not yet joined to anything.

    `ordinal` is the row's own place in the table, which fixtures reference and which never
    leaves fmsave. `owner_club_index` is a public club index, or None when the row names no
    owner. `date_58_raw` is the third date's four bytes as one little-endian int, because no
    screen has been found that names it.
    """

    ordinal: int
    uid: int
    name: str | None
    all_seater: int
    u17: int
    expansion: int
    u25: int
    owner_club_index: int | None
    b33: int
    capacity: int
    pitch_length: int
    pitch_width: int
    built: datetime.date | None
    rebuilt: datetime.date | None
    date_58_raw: int
    pitch_min_length: int
    pitch_min_width: int
    pitch_max_length: int
    pitch_max_width: int
    flags: int


@dataclass(frozen=True, slots=True, repr=False)
class StadiumIndex:
    """Every row the walk read, with the lookup the fixture join goes through.

    One index is cached and shared by every reader of a save: never mutate its mappings.

    Attributes:
        rows: Every row the walk read, in table order.
        uid_by_ordinal: The stadium uid for each table ordinal, which is what a fixture's
            stored ground resolves through. Ordinals run from one and stadium uids are unique.
        locator_hits: How many places the locator pattern matched, accepted or not, which says
            how selective the acceptance test had to be.
        reached_table_end: Whether the walk stopped where the table ends, on the closing
            header the save writes after the last row. False means the walk stopped inside the
            table and the rows past that point are missing from every count taken here.
        game_db_bytes: The length of the `game_db` the table was read from.
    """

    rows: tuple[RawStadium, ...]
    uid_by_ordinal: Mapping[int, int]
    locator_hits: int
    reached_table_end: bool
    game_db_bytes: int

    def __repr__(self) -> str:
        named_rows = sum(1 for row in self.rows if row.name is not None)
        return f"<fmsave StadiumIndex {len(self.rows)} grounds, {named_rows} named>"


@dataclass(frozen=True, slots=True)
class _StadiumTableScan:
    """Everything the walk needs from a `StadiumTableLayout`, derived once.

    `locator` matches the first three rows' ordinals one stride apart, `head_struct` unpacks
    the three fields a row is recognised by, and `row_struct` every field a row stores; both
    unpack from the row start. The `*_index` fields give each value's position in its result.
    """

    locator: re.Pattern[bytes]
    head_struct: struct.Struct
    head_ordinal_index: int
    head_uid_index: int
    head_uid_copy_index: int
    head_zero_byte_index: int
    row_struct: struct.Struct
    uid_index: int
    all_seater_index: int
    u17_index: int
    expansion_index: int
    u25_index: int
    owner_index: int
    b33_index: int
    capacity_index: int
    pitch_length_index: int
    pitch_width_index: int
    pitch_min_length_index: int
    pitch_min_width_index: int
    pitch_max_length_index: int
    pitch_max_width_index: int
    flags_index: int
    flags_offset: int
    built_offset: int
    rebuilt_offset: int
    date_58_offset: int
    row_bytes: int
    inline_name_flag: int
    name_length_offset: int
    name_offset: int
    named_row_extra_bytes: int
    lowest_name_length: int
    highest_name_length: int
    locator_rows: int
    closing_marker_offset: int
    closing_marker: bytes
    closing_uid_offset: int


@functools.cache
def _locator_pattern(row_bytes: int) -> re.Pattern[bytes]:
    """A pattern matching the words 1, 2 and 3 one row apart, for a row of `row_bytes`.

    It is cached per row length, because compiling it costs more than the search it drives.

    Raises:
        ValueError: A row is too short to hold three ordinal words one stride apart.
    """
    gap_bytes = row_bytes - 4
    if gap_bytes < 0:
        raise ValueError(f"row_bytes {row_bytes} is too short to hold an ordinal word")
    gap = b".{%d}" % gap_bytes
    words = [struct.pack("<I", ordinal) for ordinal in (1, 2, 3)]
    return re.compile(
        re.escape(words[0]) + gap + re.escape(words[1]) + gap + re.escape(words[2]),
        re.DOTALL,
    )


@functools.cache
def _stadium_table_scan(layout: StadiumTableLayout) -> _StadiumTableScan:
    """The layout's derived pattern, structs and bounds, built on first use for each layout.

    Raises:
        ValueError: Two fields overlap, a field ends past the row, the name length range
            leaves no length, or the locator row count is not positive.
    """
    head_specs = [
        (layout.ordinal_offset, "I", "ordinal"),
        (layout.uid_offset, "I", "uid"),
        (layout.uid_copy_offset, "I", "uid_copy"),
        (layout.zero_byte_offset, "B", "zero_byte"),
    ]
    row_specs = [
        (layout.uid_offset, "I", "uid"),
        (layout.all_seater_offset, "I", "all_seater"),
        (layout.u17_offset, "I", "u17"),
        (layout.expansion_offset, "I", "expansion"),
        (layout.u25_offset, "I", "u25"),
        (layout.owner_offset, "I", "owner"),
        (layout.b33_offset, "B", "b33"),
        (layout.capacity_offset, "I", "capacity"),
        (layout.pitch_length_offset, "H", "pitch_length"),
        (layout.pitch_width_offset, "H", "pitch_width"),
        (layout.pitch_min_length_offset, "H", "pitch_min_length"),
        (layout.pitch_min_width_offset, "H", "pitch_min_width"),
        (layout.pitch_max_length_offset, "H", "pitch_max_length"),
        (layout.pitch_max_width_offset, "H", "pitch_max_width"),
        (layout.flags_offset, "B", "flags"),
    ]
    head_struct, _head_start, head_indexes = build_gap_padded_struct(head_specs, start_offset=0)
    row_struct, _row_start, row_indexes = build_gap_padded_struct(row_specs, start_offset=0)
    dated_specs = [
        (layout.built_offset, _DATE_BYTES, "built"),
        (layout.rebuilt_offset, _DATE_BYTES, "rebuilt"),
        (layout.date_58_offset, _DATE_BYTES, "date_58"),
        (layout.name_length_offset, 4, "name_length"),
    ]
    for offset, field_bytes, field_name in dated_specs:
        if offset + field_bytes > layout.row_bytes:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the {layout.row_bytes}-byte "
                "stadium row"
            )
    for offset, format_code, field_name in (*head_specs, *row_specs):
        if offset + struct.calcsize(format_code) > layout.row_bytes:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the {layout.row_bytes}-byte "
                "stadium row"
            )
    lowest_name_length, highest_name_length = layout.name_length_range
    if lowest_name_length < 1 or highest_name_length < lowest_name_length:
        raise ValueError(f"name_length_range {layout.name_length_range} leaves no name length")
    if layout.locator_rows < 1:
        raise ValueError(f"locator_rows {layout.locator_rows} must be at least 1")
    return _StadiumTableScan(
        locator=_locator_pattern(layout.row_bytes),
        head_struct=head_struct,
        head_ordinal_index=head_indexes["ordinal"],
        head_uid_index=head_indexes["uid"],
        head_uid_copy_index=head_indexes["uid_copy"],
        head_zero_byte_index=head_indexes["zero_byte"],
        row_struct=row_struct,
        uid_index=row_indexes["uid"],
        all_seater_index=row_indexes["all_seater"],
        u17_index=row_indexes["u17"],
        expansion_index=row_indexes["expansion"],
        u25_index=row_indexes["u25"],
        owner_index=row_indexes["owner"],
        b33_index=row_indexes["b33"],
        capacity_index=row_indexes["capacity"],
        pitch_length_index=row_indexes["pitch_length"],
        pitch_width_index=row_indexes["pitch_width"],
        pitch_min_length_index=row_indexes["pitch_min_length"],
        pitch_min_width_index=row_indexes["pitch_min_width"],
        pitch_max_length_index=row_indexes["pitch_max_length"],
        pitch_max_width_index=row_indexes["pitch_max_width"],
        flags_index=row_indexes["flags"],
        flags_offset=layout.flags_offset,
        built_offset=layout.built_offset,
        rebuilt_offset=layout.rebuilt_offset,
        date_58_offset=layout.date_58_offset,
        row_bytes=layout.row_bytes,
        inline_name_flag=layout.inline_name_flag,
        name_length_offset=layout.name_length_offset,
        name_offset=layout.name_offset,
        named_row_extra_bytes=layout.named_row_extra_bytes,
        lowest_name_length=lowest_name_length,
        highest_name_length=highest_name_length,
        locator_rows=layout.locator_rows,
        closing_marker_offset=layout.closing_marker_offset,
        closing_marker=layout.closing_marker,
        closing_uid_offset=layout.closing_uid_offset,
    )


def find_stadium_layout(game_db_schema: int | None, build: str) -> StadiumTableLayout:
    """Look up the stadium table layout for a `game_db` schema, falling back to the build."""
    return find_layout(StadiumTableLayout, GAME_DB_SECTION, game_db_schema, build).layout


def _row_heads_at(game_db: bytes, row_offset: int, scan: _StadiumTableScan, expected: int) -> bool:
    """Whether a row with ordinal `expected` starts here: the uid doubled, then a zero byte."""
    if row_offset < 0 or row_offset + scan.row_bytes > len(game_db):
        return False
    field_values = scan.head_struct.unpack_from(game_db, row_offset)
    if field_values[scan.head_ordinal_index] != expected:
        return False
    if field_values[scan.head_uid_index] != field_values[scan.head_uid_copy_index]:
        return False
    return field_values[scan.head_zero_byte_index] == 0


def _table_starts_here(game_db: bytes, head_offset: int, scan: _StadiumTableScan) -> bool:
    """Whether `locator_rows` rows from here read ordinals 1, 2, 3 ... one stride apart."""
    for step in range(scan.locator_rows):
        if not _row_heads_at(game_db, head_offset + step * scan.row_bytes, scan, step + 1):
            return False
    return True


@dataclass(frozen=True, slots=True)
class _LocatedHead:
    """Where the table starts, and how many places the pattern matched on the way there."""

    head_offset: int | None
    locator_hits: int


def locate_stadium_table(game_db: bytes, scan: _StadiumTableScan) -> _LocatedHead:
    """The first accepted table head, and how often the pattern matched.

    The search resumes one byte past each match rather than past its end, since the pattern
    spans three rows and a real head can sit inside another match's reach.
    """
    head_offset: int | None = None
    locator_hits = 0
    cursor = 0
    search = scan.locator.search
    while True:
        found = search(game_db, cursor)
        if found is None:
            break
        locator_hits += 1
        candidate = found.start()
        if head_offset is None and _table_starts_here(game_db, candidate, scan):
            head_offset = candidate
        cursor = candidate + 1
    return _LocatedHead(head_offset, locator_hits)


def _decoded_row(
    game_db: bytes, row_offset: int, ordinal: int, name: str | None, scan: _StadiumTableScan
) -> RawStadium:
    """One row's fields, with the uid raised into the public space and the dates decoded."""
    field_values = scan.row_struct.unpack_from(game_db, row_offset)
    owner_club_index: int | None = field_values[scan.owner_index]
    if owner_club_index == MISSING_REFERENCE:
        owner_club_index = None
    return RawStadium(
        ordinal=ordinal,
        uid=field_values[scan.uid_index] + 1,
        name=name,
        all_seater=field_values[scan.all_seater_index],
        u17=field_values[scan.u17_index],
        expansion=field_values[scan.expansion_index],
        u25=field_values[scan.u25_index],
        owner_club_index=owner_club_index,
        b33=field_values[scan.b33_index],
        capacity=field_values[scan.capacity_index],
        pitch_length=field_values[scan.pitch_length_index],
        pitch_width=field_values[scan.pitch_width_index],
        built=decode_date(game_db, row_offset + scan.built_offset),
        rebuilt=decode_date(game_db, row_offset + scan.rebuilt_offset),
        date_58_raw=_WORD.unpack_from(game_db, row_offset + scan.date_58_offset)[0],
        pitch_min_length=field_values[scan.pitch_min_length_index],
        pitch_min_width=field_values[scan.pitch_min_width_index],
        pitch_max_length=field_values[scan.pitch_max_length_index],
        pitch_max_width=field_values[scan.pitch_max_width_index],
        flags=field_values[scan.flags_index],
    )


def _inline_name(
    game_db: bytes, row_offset: int, scan: _StadiumTableScan
) -> tuple[str, int] | None:
    """(name, row length) for a row carrying one, or None when the name cannot be read.

    A length outside the layout's range, a name running past the section, and text that is not
    valid UTF-8 all read as None, which ends the walk: the next row's position depends on this
    length, so a length that cannot be trusted makes every row after it unreadable too.
    """
    name_length = _WORD.unpack_from(game_db, row_offset + scan.name_length_offset)[0]
    if not scan.lowest_name_length <= name_length <= scan.highest_name_length:
        return None
    text_start = row_offset + scan.name_offset
    row_length = scan.row_bytes + scan.named_row_extra_bytes + name_length
    if row_offset + row_length > len(game_db):
        return None
    try:
        name = game_db[text_start : text_start + name_length].decode("utf-8")
    except UnicodeDecodeError:
        return None
    return name, row_length


@dataclass(frozen=True, slots=True)
class _WalkedRows:
    """The rows one walk read, and the offset it stopped at."""

    rows: list[RawStadium]
    stop_offset: int


def _walk_rows(game_db: bytes, head_offset: int, scan: _StadiumTableScan) -> _WalkedRows:
    """Step through the table from its first row, stopping at the first row that is not next."""
    rows: list[RawStadium] = []
    row_offset = head_offset
    ordinal = 1
    inline_name_flag = scan.inline_name_flag
    flags_offset = scan.flags_offset
    while not _reached_table_end(game_db, row_offset, scan, ordinal):
        if not _row_heads_at(game_db, row_offset, scan, ordinal):
            break
        name: str | None = None
        row_length = scan.row_bytes
        if game_db[row_offset + flags_offset] & inline_name_flag:
            read_name = _inline_name(game_db, row_offset, scan)
            if read_name is None:
                break
            name, row_length = read_name
        rows.append(_decoded_row(game_db, row_offset, ordinal, name, scan))
        row_offset += row_length
        ordinal += 1
    return _WalkedRows(rows, row_offset)


def _reached_table_end(
    game_db: bytes, stop_offset: int, scan: _StadiumTableScan, expected_ordinal: int
) -> bool:
    """Recognise the closing header before decoding it as a ground.

    The header repeats the next ordinal and allocation uid, followed by a fixed marker and
    a third copy of that uid. Bytes after it belong to another table, so neither a row-sized
    read nor a single word from the following data can establish the boundary.
    """
    marker_start = stop_offset + scan.closing_marker_offset
    uid_start = stop_offset + scan.closing_uid_offset
    end = max(
        scan.head_struct.size,
        scan.closing_uid_offset + _WORD.size,
        scan.closing_marker_offset + len(scan.closing_marker),
    )
    if stop_offset < 0 or stop_offset + end > len(game_db):
        return False
    values = scan.head_struct.unpack_from(game_db, stop_offset)
    uid = values[scan.head_uid_index]
    return (
        values[scan.head_ordinal_index] == expected_ordinal
        and values[scan.head_uid_copy_index] == uid
        and game_db[marker_start : marker_start + len(scan.closing_marker)] == scan.closing_marker
        and _WORD.unpack_from(game_db, uid_start)[0] == uid
    )


def read_stadium_index(game_db: bytes, layout: StadiumTableLayout, file_name: str) -> StadiumIndex:
    """Walk the stadium table and build the uid lookup the fixture join needs.

    Raises:
        ReaderCheckError: No table head was accepted, or two rows carry the same stadium uid.
            A repeated uid would merge two grounds' home clubs into one row and let whichever
            row came last claim the other's owner, so it is a raise rather than a count.
    """
    scan = _stadium_table_scan(layout)
    located = locate_stadium_table(game_db, scan)
    if located.head_offset is None:
        raise layout_mismatch(file_name, "no stadium table found")
    walked = _walk_rows(game_db, located.head_offset, scan)
    uid_by_ordinal: dict[int, int] = {}
    ordinals_by_uid: dict[int, int] = {}
    for row in walked.rows:
        if row.uid in ordinals_by_uid:
            raise layout_mismatch(file_name, "a stadium uid appears in two rows")
        ordinals_by_uid[row.uid] = row.ordinal
        uid_by_ordinal[row.ordinal] = row.uid
    return StadiumIndex(
        rows=tuple(walked.rows),
        uid_by_ordinal=FrozenMapping(uid_by_ordinal),
        locator_hits=located.locator_hits,
        reached_table_end=_reached_table_end(
            game_db, walked.stop_offset, scan, len(walked.rows) + 1
        ),
        game_db_bytes=len(game_db),
    )


def _pitch_within_limits(row: RawStadium, layout: StadiumTableLayout) -> bool:
    """Whether the pitch is a plausible length and fits inside the ground's own limits."""
    lowest_length, highest_length = layout.pitch_length_range
    return (
        lowest_length <= row.pitch_length <= highest_length
        and row.pitch_min_length <= row.pitch_length <= row.pitch_max_length
        and row.pitch_min_width <= row.pitch_width <= row.pitch_max_width
    )


@dataclass(frozen=True, slots=True)
class _TableCounts:
    """What one pass over the rows counted, before the calendar link is built."""

    named_rows: int
    owners_set: int
    owners_resolved: int
    capacity_set: int
    capacity_within_all_seater: int
    pitch_checked: int
    pitch_within_limits: int


def _table_counts(
    index: StadiumIndex, uid_by_club_index: Mapping[int, int], layout: StadiumTableLayout
) -> _TableCounts:
    """Count the rows, the owners and the two distributions the table's own gates judge.

    Every decoded ground contributes to the pitch distribution.
    """
    rows = index.rows
    named_rows = 0
    owners_set = 0
    owners_resolved = 0
    capacity_set = 0
    capacity_within_all_seater = 0
    pitch_checked = 0
    pitch_within_limits = 0
    for row in rows:
        if row.name is not None:
            named_rows += 1
        pitch_checked += 1
        if _pitch_within_limits(row, layout):
            pitch_within_limits += 1
        owner_club_index = row.owner_club_index
        if owner_club_index is not None:
            owners_set += 1
            if owner_club_index in uid_by_club_index:
                owners_resolved += 1
        if row.capacity:
            capacity_set += 1
        if row.capacity <= row.all_seater:
            capacity_within_all_seater += 1
    return _TableCounts(
        named_rows=named_rows,
        owners_set=owners_set,
        owners_resolved=owners_resolved,
        capacity_set=capacity_set,
        capacity_within_all_seater=capacity_within_all_seater,
        pitch_checked=pitch_checked,
        pitch_within_limits=pitch_within_limits,
    )


def stadium_table_stats(
    index: StadiumIndex, club_index: ClubIndex, layout: StadiumTableLayout
) -> StadiumStats:
    """What the table alone says, for the checks the shared index is enforced on.

    The three home-ground counts are zero here: they need the fixture calendar, which is read
    after this index, and the index is handed out on the strength of the table's own shape.
    """
    counts = _table_counts(index, club_index.uid_by_club_index, layout)
    return StadiumStats(
        rows=len(index.rows),
        table_end_reached=int(index.reached_table_end),
        named_rows=counts.named_rows,
        owners_set=counts.owners_set,
        owners_resolved=counts.owners_resolved,
        capacity_set=counts.capacity_set,
        capacity_within_all_seater=counts.capacity_within_all_seater,
        pitch_checked=counts.pitch_checked,
        pitch_within_limits=counts.pitch_within_limits,
        clubs_with_home_ground=0,
        owning_clubs_with_home_ground=0,
        owning_clubs_home_ground_owned=0,
    )


def home_grounds(fixtures: Sequence[Fixture], minimum_fixtures: int) -> dict[int, int]:
    """The ground each club plays most of its first-team home matches at, as club uid -> uid.

    Only a club's own first team counts: a reserve or youth side often plays elsewhere, and
    counting its matches would move the vote to a ground the club does not call home. A club
    with fewer than `minimum_fixtures` such matches in the calendar gets no entry at all, so no
    ground is called a club's home on the strength of one or two records. Two grounds used
    equally often leave the lower uid, so the answer never depends on calendar order.
    """
    votes: dict[int, dict[int, int]] = {}
    for fixture in fixtures:
        club_uid = fixture.home_club_uid
        stadium_uid = fixture.stadium_uid
        if club_uid is None or stadium_uid is None:
            continue
        if fixture.home_team_slot != _FIRST_TEAM_SLOT:
            continue
        counts = votes.setdefault(club_uid, {})
        counts[stadium_uid] = counts.get(stadium_uid, 0) + 1
    return {
        club_uid: max(counts.items(), key=lambda entry: (entry[1], -entry[0]))[0]
        for club_uid, counts in votes.items()
        if sum(counts.values()) >= minimum_fixtures
    }


def build_stadiums(
    index: StadiumIndex,
    club_index: ClubIndex,
    fixtures: Sequence[Fixture],
    layout: StadiumTableLayout,
) -> tuple[tuple[Stadium, ...], StadiumStats]:
    """Build one row per walked ground, and count what the stadium checks judge.

    The owner comes from the table and the home clubs from the calendar, which are two
    different claims about the same ground and are kept apart in the record.
    """
    uid_by_club_index = club_index.uid_by_club_index
    club_by_uid = club_index.club_by_uid
    counts = _table_counts(index, uid_by_club_index, layout)
    ground_by_club_uid = home_grounds(fixtures, layout.home_ground_minimum_fixtures)
    # The uids and the names of a ground's home clubs are taken off the same club records, so
    # the two tuples a row carries are the same length and in the same order by construction.
    home_clubs_by_stadium_uid: dict[int, list[Club]] = {}
    for club_uid, stadium_uid in ground_by_club_uid.items():
        home_club = club_by_uid.get(club_uid)
        if home_club is not None:
            home_clubs_by_stadium_uid.setdefault(stadium_uid, []).append(home_club)
    for home_clubs in home_clubs_by_stadium_uid.values():
        home_clubs.sort(key=lambda home_club: home_club.uid)

    rows: list[Stadium] = []
    owner_uid_by_stadium_uid: dict[int, int] = {}
    for raw_stadium in index.rows:
        owner_club_index = raw_stadium.owner_club_index
        owner_club_uid = (
            None if owner_club_index is None else uid_by_club_index.get(owner_club_index)
        )
        if owner_club_uid is not None:
            owner_uid_by_stadium_uid[raw_stadium.uid] = owner_club_uid
        owner_club = None if owner_club_uid is None else club_by_uid.get(owner_club_uid)
        home_clubs = home_clubs_by_stadium_uid.get(raw_stadium.uid, ())
        rows.append(
            Stadium(
                uid=raw_stadium.uid,
                name=raw_stadium.name,
                all_seater_capacity=raw_stadium.all_seater,
                expansion_capacity=raw_stadium.expansion,
                capacity=raw_stadium.capacity or None,
                owner_club_uid=owner_club_uid,
                owner_club_name=None if owner_club is None else owner_club.name,
                home_club_uids=tuple(home_club.uid for home_club in home_clubs),
                home_club_names=tuple(home_club.name for home_club in home_clubs),
                pitch_length_dm=raw_stadium.pitch_length,
                pitch_width_dm=raw_stadium.pitch_width,
                pitch_min_length_dm=raw_stadium.pitch_min_length,
                pitch_min_width_dm=raw_stadium.pitch_min_width,
                pitch_max_length_dm=raw_stadium.pitch_max_length,
                pitch_max_width_dm=raw_stadium.pitch_max_width,
                built_date=raw_stadium.built,
                rebuilt_date=raw_stadium.rebuilt,
                unknown=FrozenMapping(
                    {
                        "u17": raw_stadium.u17,
                        "u25": raw_stadium.u25,
                        "b33": raw_stadium.b33,
                        "date_58": raw_stadium.date_58_raw,
                        "flags_156": raw_stadium.flags,
                    }
                ),
            )
        )

    owning_club_uids = set(owner_uid_by_stadium_uid.values())
    owning_clubs_with_home_ground = 0
    owning_clubs_home_ground_owned = 0
    for club_uid, stadium_uid in ground_by_club_uid.items():
        if club_uid not in owning_club_uids:
            continue
        owning_clubs_with_home_ground += 1
        if owner_uid_by_stadium_uid.get(stadium_uid) == club_uid:
            owning_clubs_home_ground_owned += 1

    stats = StadiumStats(
        rows=len(index.rows),
        table_end_reached=int(index.reached_table_end),
        named_rows=counts.named_rows,
        owners_set=counts.owners_set,
        owners_resolved=counts.owners_resolved,
        capacity_set=counts.capacity_set,
        capacity_within_all_seater=counts.capacity_within_all_seater,
        pitch_checked=counts.pitch_checked,
        pitch_within_limits=counts.pitch_within_limits,
        clubs_with_home_ground=len(ground_by_club_uid),
        owning_clubs_with_home_ground=owning_clubs_with_home_ground,
        owning_clubs_home_ground_owned=owning_clubs_home_ground_owned,
    )
    return tuple(rows), stats
