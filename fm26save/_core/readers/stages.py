"""The stage table near the end of `game_db`, and the joins it carries to competitions.

The table is a run of fixed-size rows sitting in the last stretch of `game_db`. A row stores
its stage id twice, which is what makes the table recognisable: the reader searches the tail
of the section for the first offset where a long chain of rows all decode, walks back to the
head of that chain, and then steps row by row. A row that does not decode is a gap, and the
walk scans forward one byte at a time for the next row that does, so it resynchronises without
ever guessing a stride.

Every offset, the stride, the chain length and the bounds come from the layout, derived once
per layout, so the walk itself reads no layout fields.
"""

from __future__ import annotations

import functools
import itertools
import struct
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import StageTableLayout, find_layout
from fm26save._core._reader_stats import StageStats
from fm26save._core.models.common import CodedValue
from fm26save._core.models.competitions import CompetitionRound, Stage
from fm26save._core.readers._common import (
    GAME_DB_SECTION,
    MISSING_REFERENCE,
    build_gap_padded_struct,
    layout_mismatch,
)


@dataclass(frozen=True, slots=True, repr=False)
class StageIndex:
    """Every stage row, with the lookups other readers join through.

    One index is cached and shared by every reader of a save: never mutate its mappings.

    Attributes:
        stages: Every stage the walk read, in the order the table stores them.
        stage_by_id: The stage for each stage id. Stage ids are unique.
        competition_id_by_stage_id: The competition of each stage that has one, so a fixture
            or a table group reaches its competition in one hop.
        stage_ids_by_competition_id: The stage ids of each competition, in table order.
        stats: What the walk counted, for the stage checks.
        game_db_bytes: The length of the `game_db` the table was read from.
    """

    stages: tuple[Stage, ...]
    stage_by_id: Mapping[int, Stage]
    competition_id_by_stage_id: Mapping[int, int]
    stage_ids_by_competition_id: Mapping[int, tuple[int, ...]]
    stats: StageStats
    game_db_bytes: int

    def __repr__(self) -> str:
        return (
            f"<fmsave StageIndex {len(self.stages)} stages, "
            f"{len(self.stage_ids_by_competition_id)} competitions>"
        )


@dataclass(frozen=True, slots=True)
class _StageTableScan:
    """Everything the walk needs from a `StageTableLayout`, derived once.

    `validity_struct` unpacks the fields a row is recognised by, and `row_struct` every field
    a row stores; both unpack from the row start. The `*_index` fields give each value's
    position in its result. `zero_byte_offset` is where the zero byte sits in the row, which
    the prefilter reads straight from the layout rather than assuming it is the last of the
    fields a row is recognised by.
    """

    validity_struct: struct.Struct
    validity_previous_index: int
    validity_stage_id_index: int
    validity_stage_id_copy_index: int
    validity_zero_byte_index: int
    zero_byte_offset: int
    row_struct: struct.Struct
    previous_index: int
    stage_id_index: int
    competition_id_index: int
    group_id_index: int
    round_index: int
    unknown_s25_index: int
    unknown_s29_index: int
    row_bytes: int
    chain_rows: int
    search_bytes: int
    max_search_bytes: int | None
    resynchronisation_bytes: int
    lowest_stage_id: int
    highest_stage_id: int
    competition_id_limit: int


@functools.cache
def _stage_table_scan(layout: StageTableLayout) -> _StageTableScan:
    """The layout's derived structs and bounds, built on first use for each layout.

    Raises:
        ValueError: Two fields overlap, a field starts before the row start or ends past the
            row, the stage id range leaves no id, the chain length or the competition id
            limit is not positive, or the widest search window is narrower than the first.
    """
    validity_specs = [
        (layout.previous_stage_id_offset, "I", "previous_stage_id"),
        (layout.stage_id_offset, "I", "stage_id"),
        (layout.stage_id_copy_offset, "I", "stage_id_copy"),
        (layout.zero_byte_offset, "B", "zero_byte"),
    ]
    row_specs = [
        *validity_specs[:3],
        (layout.competition_id_offset, "I", "competition_id"),
        (layout.group_id_offset, "I", "group_id"),
        (layout.round_offset, "I", "round"),
        (layout.unknown_s25_offset, "I", "unknown_s25"),
        (layout.unknown_s29_offset, "I", "unknown_s29"),
    ]
    validity_struct, _validity_start, validity_indexes = build_gap_padded_struct(
        validity_specs, start_offset=0
    )
    row_struct, _row_start, row_indexes = build_gap_padded_struct(row_specs, start_offset=0)
    for offset, format_code, field_name in (*validity_specs, *row_specs):
        if offset + struct.calcsize(format_code) > layout.row_bytes:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the {layout.row_bytes}-byte "
                "stage row"
            )
    lowest_stage_id, highest_stage_id = layout.stage_id_exclusive_range
    if highest_stage_id - lowest_stage_id < 2:
        raise ValueError(
            f"stage_id_exclusive_range {layout.stage_id_exclusive_range} leaves no stage id "
            "strictly between its bounds"
        )
    if layout.chain_rows < 1:
        raise ValueError(f"chain_rows {layout.chain_rows} must be at least 1")
    if layout.competition_id_limit < 1:
        raise ValueError(f"competition_id_limit {layout.competition_id_limit} must be at least 1")
    if layout.max_search_bytes is not None and layout.max_search_bytes < layout.search_bytes:
        raise ValueError(
            f"max_search_bytes {layout.max_search_bytes} is narrower than search_bytes "
            f"{layout.search_bytes}"
        )
    return _StageTableScan(
        validity_struct=validity_struct,
        validity_previous_index=validity_indexes["previous_stage_id"],
        validity_stage_id_index=validity_indexes["stage_id"],
        validity_stage_id_copy_index=validity_indexes["stage_id_copy"],
        validity_zero_byte_index=validity_indexes["zero_byte"],
        zero_byte_offset=layout.zero_byte_offset,
        row_struct=row_struct,
        previous_index=row_indexes["previous_stage_id"],
        stage_id_index=row_indexes["stage_id"],
        competition_id_index=row_indexes["competition_id"],
        group_id_index=row_indexes["group_id"],
        round_index=row_indexes["round"],
        unknown_s25_index=row_indexes["unknown_s25"],
        unknown_s29_index=row_indexes["unknown_s29"],
        row_bytes=layout.row_bytes,
        chain_rows=layout.chain_rows,
        search_bytes=layout.search_bytes,
        max_search_bytes=layout.max_search_bytes,
        resynchronisation_bytes=layout.resynchronisation_bytes,
        lowest_stage_id=lowest_stage_id,
        highest_stage_id=highest_stage_id,
        competition_id_limit=layout.competition_id_limit,
    )


def find_stage_layout(game_db_schema: int | None, build: str) -> StageTableLayout:
    """Look up the stage table layout for a `game_db` schema, falling back to the build."""
    return find_layout(StageTableLayout, GAME_DB_SECTION, game_db_schema, build).layout


def _row_decodes(
    game_db: bytes, row_offset: int, scan: _StageTableScan, buffer_length: int
) -> bool:
    """Whether a stage row starts here: the id stored twice, in range, after a zero byte."""
    if row_offset < 0 or row_offset + scan.row_bytes > buffer_length:
        return False
    field_values = scan.validity_struct.unpack_from(game_db, row_offset)
    if field_values[scan.validity_zero_byte_index] != 0:
        return False
    stage_id: int = field_values[scan.validity_stage_id_index]
    if field_values[scan.validity_stage_id_copy_index] != stage_id:
        return False
    if not scan.lowest_stage_id < stage_id < scan.highest_stage_id:
        return False
    previous_stage_id: int = field_values[scan.validity_previous_index]
    return previous_stage_id in (stage_id - 1, MISSING_REFERENCE)


def _chain_starts_here(
    game_db: bytes, row_offset: int, scan: _StageTableScan, buffer_length: int
) -> bool:
    """Whether `chain_rows` rows all decode from here, one stride apart."""
    for step in range(scan.chain_rows):
        if not _row_decodes(game_db, row_offset + step * scan.row_bytes, scan, buffer_length):
            return False
    return True


def _chain_id_steps(game_db: bytes, row_offset: int, scan: _StageTableScan) -> int:
    """How many rows of the chain from here hold the id one above the row before."""
    unpack = scan.validity_struct.unpack_from
    stage_ids = [
        unpack(game_db, row_offset + step * scan.row_bytes)[scan.validity_stage_id_index]
        for step in range(scan.chain_rows)
    ]
    return sum(later == earlier + 1 for earlier, later in itertools.pairwise(stage_ids))


def find_table_start(game_db: bytes, scan: _StageTableScan) -> int | None:
    """The offset of the table's first row, or None when no chain of rows is found.

    The search covers the last `search_bytes` of `game_db`, since the table sits at the end of
    the section. When no chain starts there, the window doubles until it reaches
    `max_search_bytes`, or the start of `game_db` when that is None, and each doubling
    searches only the stretch it adds, so a save whose table sits near the end pays for the
    first window alone and no offset is tried twice.

    The first offset that starts a full chain is found one byte at a time, and the head is then
    reached by stepping back while the row before still decodes, so rows before the chain are
    kept.

    A chain can also decode one byte out of step with the real rows: both copies of the id
    shift together, so every id reads as the real one times 256 and still passes. Every offset
    within one row of the first chain is therefore compared, and the chain whose ids most often
    step up by one, as real stage ids do, is kept.
    """
    buffer_length = len(game_db)
    searched_from = buffer_length
    window_bytes = scan.search_bytes
    while searched_from > 0:
        window_start = max(0, buffer_length - window_bytes)
        table_start = _find_table_start_between(game_db, scan, window_start, searched_from)
        if table_start is not None:
            return table_start
        if scan.max_search_bytes is not None and window_bytes >= scan.max_search_bytes:
            return None
        searched_from = window_start
        window_bytes *= 2
        if scan.max_search_bytes is not None:
            window_bytes = min(window_bytes, scan.max_search_bytes)
    return None


def _find_table_start_between(
    game_db: bytes, scan: _StageTableScan, first_candidate: int, candidates_end: int
) -> int | None:
    """The table's first row, for a chain starting in [first_candidate, candidates_end)."""
    buffer_length = len(game_db)
    row_bytes = scan.row_bytes
    zero_byte_offset_in_row = scan.zero_byte_offset
    candidate = first_candidate
    last_candidate = min(candidates_end, buffer_length - row_bytes + 1)
    while candidate < last_candidate:
        # The zero byte rules out all but one candidate in 256 before anything is unpacked.
        if (
            game_db[candidate + zero_byte_offset_in_row] == 0
            and _row_decodes(game_db, candidate, scan, buffer_length)
            and _chain_starts_here(game_db, candidate, scan, buffer_length)
        ):
            chains = [
                offset
                for offset in range(candidate, min(candidate + row_bytes, buffer_length))
                if _chain_starts_here(game_db, offset, scan, buffer_length)
            ]
            table_start = max(chains, key=lambda offset: _chain_id_steps(game_db, offset, scan))
            while _row_decodes(game_db, table_start - row_bytes, scan, buffer_length):
                table_start -= row_bytes
            return table_start
        candidate += 1
    return None


@dataclass(frozen=True, slots=True)
class _WalkedRows:
    """The rows one walk read, the gaps it stepped over, and where it stopped."""

    rows: list[tuple[int, ...]]
    gaps: int
    table_end: int


def _walk_rows(game_db: bytes, table_start: int, scan: _StageTableScan) -> _WalkedRows:
    """Step through the table from its first row, resynchronising over anything that is not one."""
    buffer_length = len(game_db)
    row_bytes = scan.row_bytes
    zero_byte_offset_in_row = scan.zero_byte_offset
    unpack_row = scan.row_struct.unpack_from
    rows: list[tuple[int, ...]] = []
    gaps = 0
    row_offset = table_start
    table_end = table_start
    while row_offset + row_bytes <= buffer_length:
        if _row_decodes(game_db, row_offset, scan, buffer_length):
            rows.append(unpack_row(game_db, row_offset))
            row_offset += row_bytes
            table_end = row_offset
            continue
        resynchronised_at = -1
        candidate = row_offset + 1
        furthest_candidate = min(
            row_offset + scan.resynchronisation_bytes, buffer_length - row_bytes
        )
        while candidate <= furthest_candidate:
            if game_db[candidate + zero_byte_offset_in_row] == 0 and _row_decodes(
                game_db, candidate, scan, buffer_length
            ):
                resynchronised_at = candidate
                break
            candidate += 1
        if resynchronised_at < 0:
            break
        gaps += 1
        row_offset = resynchronised_at
    return _WalkedRows(rows, gaps, table_end)


def read_stage_index(game_db: bytes, layout: StageTableLayout, file_name: str) -> StageIndex:
    """Walk the stage table and build the index every competition join goes through.

    Raises:
        ReaderCheckError: No stage table was found in the tail of `game_db`, or a stage id
            appears in two rows.
        ValueError: The layout is inconsistent (see `_stage_table_scan`).
    """
    scan = _stage_table_scan(layout)
    table_start = find_table_start(game_db, scan)
    if table_start is None:
        searched = (
            "game_db"
            if scan.max_search_bytes is None
            else f"the last {scan.max_search_bytes:,} bytes of game_db"
        )
        raise layout_mismatch(file_name, f"no stage table was found in {searched}")
    walked = _walk_rows(game_db, table_start, scan)

    stages: list[Stage] = []
    stage_by_id: dict[int, Stage] = {}
    competition_id_by_stage_id: dict[int, int] = {}
    stage_ids_by_competition: dict[int, list[int]] = {}
    competition_id_rejected = 0
    trailing_sentinel_ok = 0
    ascending_steps = 0
    previous_stage_id_seen: int | None = None
    competition_id_limit = scan.competition_id_limit
    for field_values in walked.rows:
        stage_id: int = field_values[scan.stage_id_index]
        if stage_id in stage_by_id:
            raise layout_mismatch(file_name, f"stage id {stage_id} appears in two stage rows")
        stored_competition_id: int = field_values[scan.competition_id_index]
        competition_id: int | None = stored_competition_id
        if stored_competition_id == MISSING_REFERENCE:
            competition_id = None
        elif stored_competition_id >= competition_id_limit:
            competition_id = None
            competition_id_rejected += 1
        stored_group_id: int = field_values[scan.group_id_index]
        stored_round_code: int = field_values[scan.round_index]
        stored_previous_stage_id: int = field_values[scan.previous_index]
        unknown_s25: int = field_values[scan.unknown_s25_index]
        unknown_s29: int = field_values[scan.unknown_s29_index]
        if unknown_s29 == MISSING_REFERENCE:
            trailing_sentinel_ok += 1
        stage = Stage(
            id=stage_id,
            competition_id=competition_id,
            competition_name=None,
            group_id=None if stored_group_id == MISSING_REFERENCE else stored_group_id,
            round=(
                None
                if stored_round_code == MISSING_REFERENCE
                else CodedValue.from_raw(CompetitionRound, stored_round_code)
            ),
            previous_stage_id=(
                None if stored_previous_stage_id == MISSING_REFERENCE else stored_previous_stage_id
            ),
            unknown=FrozenMapping({"s25": unknown_s25, "s29": unknown_s29}),
        )
        stages.append(stage)
        stage_by_id[stage_id] = stage
        if competition_id is not None:
            competition_id_by_stage_id[stage_id] = competition_id
            stage_ids_by_competition.setdefault(competition_id, []).append(stage_id)
        if previous_stage_id_seen is not None and stage_id > previous_stage_id_seen:
            ascending_steps += 1
        previous_stage_id_seen = stage_id

    row_count = len(stages)
    stats = StageStats(
        rows=row_count,
        gaps=walked.gaps,
        ascending_steps=ascending_steps,
        steps=max(row_count - 1, 0),
        with_competition=len(competition_id_by_stage_id),
        competition_id_rejected=competition_id_rejected,
        trailing_sentinel_ok=trailing_sentinel_ok,
        bytes_after_table=len(game_db) - walked.table_end,
    )
    return StageIndex(
        stages=tuple(stages),
        stage_by_id=stage_by_id,
        competition_id_by_stage_id=competition_id_by_stage_id,
        stage_ids_by_competition_id={
            competition_id: tuple(stage_ids)
            for competition_id, stage_ids in stage_ids_by_competition.items()
        },
        stats=stats,
        game_db_bytes=len(game_db),
    )


def named_stages(
    stages: tuple[Stage, ...], name_for: Callable[[int | None], str | None]
) -> tuple[Stage, ...]:
    """The same stage rows with `competition_name` filled in.

    `name_for` is `CompetitionIndex.name_for`, the one lookup that names a competition, so a
    stage is named by exactly the rule that names its competition and this module repeats none
    of it. The bound method is passed rather than the index holding it, which keeps this module
    free of an import back from the competitions reader, which already imports this one.
    """
    return tuple(
        replace(stage, competition_name=name_for(stage.competition_id)) for stage in stages
    )
