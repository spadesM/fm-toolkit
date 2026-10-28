"""One streamed pass over the unnamed span: fixtures, tables, rules preambles, results.

All four structures share one unnamed region, around 200 MB decompressed on a full save, so
they are collected together instead of one pass each. The region is never buffered whole:
frames arrive one at a time and each is scanned as `carry + frame`, where the carry is the
last `SPAN_CARRY_OVER_BYTES` of the previous window and is far longer than the longest
record. A candidate whose bytes do not all lie inside its window is left alone, because the
next window's carry holds it whole; each structure remembers the greatest region-relative
offset it has already considered, so a candidate that appears in two windows is considered
exactly once, and every search starts far enough into the carry that only candidates which
could straddle the boundary are looked at twice.

Where a structure has a variable length, leaving a candidate alone also ends the scan of
that window: a later candidate might still be judged where this one cannot, and judging it
would carry the high-water mark past the deferred candidate and hide it from the next window
for good. A fixture record is a fixed length, so no later record can fit where an earlier one
does not, and its scan runs to the end of the window.

Each search's pattern, struct, offsets and bounds are derived from its layout once per
layout, so the scan loops never read a layout. The pass keeps raw words: it decodes no
kick-off time and joins no id, which is what the fixtures, league-tables and rules readers
are for. Region-relative offsets stay on these private records and are never public.

The result search is the one that cannot finish its job here. Whether a result record is in
scope depends on the fixture calendar's dates and on the stage table, and neither exists while
this pass runs, so it collects only what a record settles by itself and the results reader
applies the rest. That is why these records carry no span offset: nothing downstream separates
them by position.
"""

from __future__ import annotations

import datetime
import functools
import re
import struct
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from fm26save._core._container import RETRY_HINT
from fm26save._core._errors import ISSUES_URL, CorruptSaveError, ReaderCheckError
from fm26save._core._layouts import (
    SPAN_CARRY_OVER_BYTES,
    FixtureCalendarLayout,
    LeagueTableLayout,
    RulesPreambleLayout,
    StageResultLayout,
    find_layout,
)
from fm26save._core._scan import decode_date
from fm26save._core.readers._common import (
    MISSING_REFERENCE,
    SPAN_REGION,
    build_gap_padded_struct,
    year_bytes_pattern,
)
from fm26save._core.readers.results import (
    RawStageResult,
    collect_results,
    find_result_layout,
    result_search,
)

SPAN_RECORDS_CACHE_KEY = "span_records"

_UINT16 = struct.Struct("<H")
_UINT32 = struct.Struct("<I")
_KICK_OFF_YEAR_AFTER_DATE = 2


@dataclass(frozen=True, slots=True)
class RawTableRow:
    """One 17-byte row of a league-table block, as stored.

    `key` is the opponent's first-team id, or the layout's unplayed key on an aggregate row
    and in a match slot that was never played.
    """

    key: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    points: int
    flag: int


@dataclass(frozen=True, slots=True)
class RawFixture:
    """One fixture calendar record, as stored, with its region-relative offset.

    The kick-off date is kept as the two raw words the record holds, `packed_kick_off` (the
    day of the year and the time slot) and `kick_off_year`, so the pass does no date
    arithmetic. `round_index` is raw, so the layout's no-round value still reads as itself.
    """

    span_offset: int
    stage_id: int | None
    stadium_ordinal: int | None
    home_team_id: int
    away_team_id: int
    packed_kick_off: int
    kick_off_year: int
    season_start_year: int | None
    match_record_id: int | None
    round_index: int
    played: bool
    date2: int
    phase: int
    leg: int
    r39_42: int
    match_rules_template: tuple[int, int, int]
    r47_54: int


@dataclass(frozen=True, slots=True)
class RawFixtureContinuation:
    """Provisional calendar rows framed exactly between two original strict anchors."""

    left_offset: int
    right_offset: int
    fixtures: tuple[RawFixture, ...]


@dataclass(frozen=True, slots=True)
class RawTableBlock:
    """One league-table block, as stored, with its region-relative offset.

    `aggregates` holds the five rows in their stored order: total, home, away, first half,
    second half. `matches` holds two rows per round, whose venue alternates with the slot's
    parity. `team_id` is the first-team id of the club the block belongs to, which the block
    itself does not guarantee to be a real team.
    """

    span_offset: int
    team_id: int
    head_bytes: tuple[int, ...]
    aggregates: tuple[RawTableRow, ...]
    rounds_per_venue: int
    matches: tuple[RawTableRow, ...]


@dataclass(frozen=True, slots=True)
class RawRulesRound:
    """One round of a competition-rules preamble, as stored.

    `number` is the stored byte plus one. A round the save does not number stores the
    layout's `round_no_number_value` of 255, so it reads here as 256 rather than as a guess.
    The rules reader is what maps that value, which is why the layout registers it although
    nothing in this pass reads it: a later reader must not mistake 256 for a real round.

    `match_count` retains an unidentified u32 under its legacy name, not a reliable match
    count: the same dated row can change from 2 to 10 as a career advances.
    """

    number: int
    date: datetime.date | None
    match_count: int
    kind: int
    b5: int


@dataclass(frozen=True, slots=True)
class RawRulesBlock:
    """One competition-rules preamble block, as stored, with its region-relative offset.

    The four promotion-quad values are None together when the save's two copies of the quad
    differ. A block's club count and its points deduction for administration are not here at
    all: no fixed offset from the marker carries either on the corpus, so the span pass does
    not guess them.
    `fully_parsed` is true when the quad was doubled and the tie-break list, the prize list
    and every round record decoded. It therefore holds on a smaller share of blocks than the
    figure the format research recorded, which counts the lists and the rounds and ignores
    the quad: a gate on this field must say which of the two definitions it means.
    """

    span_offset: int
    promotion_places: int | None
    playoff_places: int | None
    promotion_byte2: int | None
    relegation_places: int | None
    tie_breaks: tuple[int, ...]
    prize_money: tuple[int, ...]
    rounds: tuple[RawRulesRound, ...]
    fully_parsed: bool


@dataclass(frozen=True, slots=True)
class RawFixtureScore:
    """A counted packet's score for its following physical fixture record.

    Both goals are None when the packet's score fields are unsafe. This retains rejected
    score evidence without changing the structural fixture path or another score source.
    """

    span_offset: int
    home_goals: int | None
    away_goals: int | None


@dataclass(frozen=True, slots=True)
class RawFixturePresence:
    """The result-presence prefix owned by one complete physical fixture record."""

    span_offset: int
    played: bool


@dataclass(frozen=True, slots=True, repr=False)
class SpanRecords:
    """What one pass over the unnamed span found. The repr gives counts only.

    The four counters count the candidates each search judged, accepted or not, so a reader
    that gates on an accept rate divides by them instead of walking the span a second time.
    They are not counts of raw pattern matches: a candidate whose bytes run past the end of
    the last window is never judged, so it is never counted either.

    `rules_markers` is the exception to that reading. Every marker judged yields a block, so
    it always equals `len(rules_blocks)` and an accept rate built from it is 1 by
    construction; it is the denominator for the share of blocks that fully parsed, not for a
    rejection rate.

    `results` is the other exception, in the opposite direction. These records are collected on
    what each one settles by itself, because the calendar and the stage table that decide the
    rest have not been read when this pass runs, so the tuple holds candidates the results
    reader may still turn away. It is not a set of accepted records.
    """

    fixtures: tuple[RawFixture, ...]
    table_blocks: tuple[RawTableBlock, ...]
    rules_blocks: tuple[RawRulesBlock, ...]
    results: tuple[RawStageResult, ...]
    fixture_candidates: int
    table_block_candidates: int
    rules_markers: int
    result_candidates: int
    span_bytes: int
    frame_count: int
    fixture_continuations: tuple[RawFixtureContinuation, ...] = ()
    fixture_scores: tuple[RawFixtureScore, ...] = ()
    fixture_presence: tuple[RawFixturePresence, ...] = ()
    fixture_cache_offsets: tuple[int, ...] = ()

    def __repr__(self) -> str:
        return (
            f"<fmsave SpanRecords {len(self.fixtures)} fixtures, "
            f"{len(self.table_blocks)} table blocks, {len(self.rules_blocks)} rules blocks, "
            f"{len(self.results)} results>"
        )


@dataclass(frozen=True, slots=True)
class SpanLayouts:
    """The layouts and the carry-over size one span pass uses."""

    fixtures: FixtureCalendarLayout
    tables: LeagueTableLayout
    rules: RulesPreambleLayout
    results: StageResultLayout
    carry_over_bytes: int


def find_span_layouts(build: str) -> SpanLayouts:
    """Look up the four span layouts for a build. The span carries no schema number."""
    return SpanLayouts(
        fixtures=find_layout(FixtureCalendarLayout, SPAN_REGION, None, build).layout,
        tables=find_layout(LeagueTableLayout, SPAN_REGION, None, build).layout,
        rules=find_layout(RulesPreambleLayout, SPAN_REGION, None, build).layout,
        results=find_result_layout(build),
        carry_over_bytes=SPAN_CARRY_OVER_BYTES,
    )


def _span_decode_error(file_name: str, error: Exception) -> CorruptSaveError:
    """A read ran past its window, which the acceptance checks should have caught."""
    return CorruptSaveError(
        f"{file_name}: region {SPAN_REGION!r} is damaged or was being written ({error}). "
        f"{RETRY_HINT}"
    )


def missing_clock_error(file_name: str) -> ReaderCheckError:
    """The span pass needs the in-game date to build its kick-off year window."""
    return ReaderCheckError(
        f"{file_name}: region {SPAN_REGION!r}: the save's in-game date could not be read, so "
        f"the kick-off year window cannot be built. Please report it at {ISSUES_URL}"
    )


@dataclass(frozen=True, slots=True)
class _FixtureSearch:
    """Everything the fixture scan needs from a `FixtureCalendarLayout` and the clock."""

    pattern: re.Pattern[bytes]
    match_offset: int
    record_bytes: int
    marker_byte_offset: int
    marker_byte_value: int
    sentinel_offsets: tuple[tuple[int, int], ...]
    fields_struct: struct.Struct
    struct_start: int
    core_struct: struct.Struct
    core_start: int
    core_end: int
    stage_id_index: int
    stadium_ordinal_index: int
    home_team_id_index: int
    away_team_id_index: int
    packed_kick_off_index: int
    kick_off_year_index: int
    date2_index: int
    season_start_year_index: int
    match_record_id_index: int
    phase_index: int
    leg_index: int
    round_index_index: int
    r39_42_index: int
    match_rules_template_index: int
    r47_54_index: int
    played_index: int
    lowest_team_id: int
    highest_team_id: int
    search_back_bytes: int


@dataclass(frozen=True, slots=True)
class _TableSearch:
    """Everything the league-table scan needs from a `LeagueTableLayout`."""

    pattern: re.Pattern[bytes]
    row_bytes: int
    aggregate_count: int
    team_id_offset: int
    head_bytes_offset: int
    head_bytes_count: int
    rounds_per_venue_offset: int
    matches_offset: int
    lowest_rounds_per_venue: int
    highest_rounds_per_venue: int
    row_struct: struct.Struct
    key_index: int
    played_index: int
    played_copy_index: int
    won_index: int
    drawn_index: int
    lost_index: int
    goals_for_index: int
    goals_against_index: int
    points_index: int
    flag_index: int
    lowest_offset: int
    search_back_bytes: int


@dataclass(frozen=True, slots=True)
class _RulesSearch:
    """Everything the rules-preamble scan needs from a `RulesPreambleLayout`."""

    marker: bytes
    promotion_quad_offset: int
    promotion_quad_bytes: int
    body_offset: int
    tie_break_count_max: int
    prize_count_max: int
    round_count_max: int
    round_record_bytes: int
    round_anchor_search_bytes: int
    round_kind_offset: int
    round_date_offset: int
    round_b5_offset: int
    round_number_offset: int
    round_match_count_offset: int
    round_match_count_max: int
    round_ordinal_offset: int
    round_indexed_kind_value: int
    moved_match_bytes: int
    moved_match_sentinel_offset: int
    moved_match_sentinel_value: int
    round_interstitial_tag_offset: int
    round_interstitial_tag_value: int
    moved_match_tail_offset: int
    moved_match_tail: bytes
    moved_match_max_per_round: int
    search_back_bytes: int


def _byte_run(count: int) -> bytes:
    return b".{%d}" % count


@functools.cache
def _fixture_search(layout: FixtureCalendarLayout, clock_year: int) -> _FixtureSearch:
    """The fixture pattern and struct for one layout and in-game year, built on first use.

    Raises:
        ValueError: The layout does not describe two ascending sentinel bytes before the
            kick-off year, the years around the clock are none, or two record fields
            overlap.
    """
    sentinels = tuple(sorted(layout.sentinel_offsets))
    if len(sentinels) != 2:
        raise ValueError("a fixture record is located by exactly two sentinel bytes")
    (first_offset, first_value), (second_offset, second_value) = sentinels
    year_low_offset = layout.kick_off_date_offset + _KICK_OFF_YEAR_AFTER_DATE
    if not 0 <= first_offset < second_offset < year_low_offset:
        raise ValueError(
            f"the sentinel offsets {sentinels} must be at or after the record start and "
            f"before the kick-off year at offset {year_low_offset}"
        )
    years = range(clock_year - layout.years_before_clock, clock_year + layout.years_after_clock + 1)
    pattern = re.compile(
        re.escape(bytes((first_value,)))
        + _byte_run(second_offset - first_offset - 1)
        + re.escape(bytes((second_value,)))
        + _byte_run(year_low_offset - second_offset - 1)
        + year_bytes_pattern(years),
        re.DOTALL,
    )
    template_code = f"{layout.match_rules_template_bytes}s"
    fields = [
        (layout.stage_id_offset, "I", "stage_id"),
        (layout.stadium_ordinal_offset, "I", "stadium_ordinal"),
        (layout.home_team_id_offset, "I", "home_team_id"),
        (layout.away_team_id_offset, "I", "away_team_id"),
        (layout.kick_off_date_offset, "H", "packed_kick_off"),
        (year_low_offset, "H", "kick_off_year"),
        (layout.date2_offset, "I", "date2"),
        (layout.season_start_year_offset, "H", "season_start_year"),
        (layout.match_record_id_offset, "I", "match_record_id"),
        (layout.phase_offset, "B", "phase"),
        (layout.leg_offset, "B", "leg"),
        (layout.round_index_offset, "B", "round_index"),
        (layout.r39_42_offset, "I", "r39_42"),
        (layout.match_rules_template_offset, template_code, "match_rules_template"),
        (layout.r47_54_offset, "Q", "r47_54"),
        (layout.played_offset, "B", "played"),
    ]
    fields_struct, struct_start, index_by_name = build_gap_padded_struct(fields)
    core_struct, core_start, core_indices = build_gap_padded_struct(
        [entry for entry in fields if entry[2] != "played"]
    )
    core_end = core_start + core_struct.size
    if (
        core_end != layout.played_offset
        or core_start != struct_start
        or any(index_by_name[name] != index for name, index in core_indices.items())
    ):
        raise ValueError("the following fixture prefix must start immediately after the core")
    lowest_team_id, highest_team_id = layout.team_id_range
    return _FixtureSearch(
        pattern=pattern,
        match_offset=first_offset,
        record_bytes=layout.record_bytes,
        marker_byte_offset=layout.marker_byte_offset,
        marker_byte_value=layout.marker_byte_value,
        sentinel_offsets=sentinels,
        fields_struct=fields_struct,
        struct_start=struct_start,
        core_struct=core_struct,
        core_start=core_start,
        core_end=core_end,
        stage_id_index=index_by_name["stage_id"],
        stadium_ordinal_index=index_by_name["stadium_ordinal"],
        home_team_id_index=index_by_name["home_team_id"],
        away_team_id_index=index_by_name["away_team_id"],
        packed_kick_off_index=index_by_name["packed_kick_off"],
        kick_off_year_index=index_by_name["kick_off_year"],
        date2_index=index_by_name["date2"],
        season_start_year_index=index_by_name["season_start_year"],
        match_record_id_index=index_by_name["match_record_id"],
        phase_index=index_by_name["phase"],
        leg_index=index_by_name["leg"],
        round_index_index=index_by_name["round_index"],
        r39_42_index=index_by_name["r39_42"],
        match_rules_template_index=index_by_name["match_rules_template"],
        r47_54_index=index_by_name["r47_54"],
        played_index=index_by_name["played"],
        lowest_team_id=lowest_team_id,
        highest_team_id=highest_team_id,
        search_back_bytes=layout.record_bytes - layout.marker_byte_offset,
    )


@functools.cache
def _table_search(layout: LeagueTableLayout) -> _TableSearch:
    """The league-table pattern and row struct for one layout, built on first use.

    Raises:
        ValueError: The row key does not start a row, the layout has fewer than two
            aggregate rows, or two row fields overlap.
    """
    if layout.key_offset != 0:
        raise ValueError("the row key must start a row, since the aggregate rows locate a block")
    if layout.aggregate_count < 2:
        raise ValueError("a block is located by at least two aggregate rows")
    key_bytes = _UINT32.pack(layout.unplayed_key)
    keyed_row = re.escape(key_bytes) + _byte_run(layout.row_bytes - _UINT32.size)
    pattern = re.compile(keyed_row * (layout.aggregate_count - 1) + re.escape(key_bytes), re.DOTALL)
    row_struct, _row_start, index_by_name = build_gap_padded_struct(
        [
            (layout.key_offset, "I", "key"),
            (layout.played_offset, "B", "played"),
            (layout.played_copy_offset, "B", "played_copy"),
            (layout.won_offset, "B", "won"),
            (layout.drawn_offset, "B", "drawn"),
            (layout.lost_offset, "B", "lost"),
            (layout.zero_offset, "B", "zero"),
            (layout.goals_for_offset, "H", "goals_for"),
            (layout.goals_against_offset, "H", "goals_against"),
            (layout.points_offset, "H", "points"),
            (layout.flag_offset, "B", "flag"),
        ],
        start_offset=0,
    )
    lowest_rounds, highest_rounds = layout.rounds_per_venue_range
    lowest_offset = min(layout.team_id_offset, layout.head_bytes_offset)
    longest_block = layout.matches_offset + layout.row_bytes * 2 * highest_rounds - lowest_offset
    return _TableSearch(
        pattern=pattern,
        row_bytes=layout.row_bytes,
        aggregate_count=layout.aggregate_count,
        team_id_offset=layout.team_id_offset,
        head_bytes_offset=layout.head_bytes_offset,
        head_bytes_count=layout.head_bytes_count,
        rounds_per_venue_offset=layout.rounds_per_venue_offset,
        matches_offset=layout.matches_offset,
        lowest_rounds_per_venue=lowest_rounds,
        highest_rounds_per_venue=highest_rounds,
        row_struct=row_struct,
        key_index=index_by_name["key"],
        played_index=index_by_name["played"],
        played_copy_index=index_by_name["played_copy"],
        won_index=index_by_name["won"],
        drawn_index=index_by_name["drawn"],
        lost_index=index_by_name["lost"],
        goals_for_index=index_by_name["goals_for"],
        goals_against_index=index_by_name["goals_against"],
        points_index=index_by_name["points"],
        flag_index=index_by_name["flag"],
        lowest_offset=lowest_offset,
        search_back_bytes=longest_block,
    )


@functools.cache
def _rules_search(layout: RulesPreambleLayout) -> _RulesSearch:
    """The rules-preamble marker and bounds for one layout, built on first use.

    Raises:
        ValueError: The marker is empty, or the body does not start after it.
    """
    if not layout.marker:
        raise ValueError("the rules marker must not be empty")
    if layout.body_offset < len(layout.marker):
        raise ValueError("the rules body must start at or after the end of the marker")
    longest_round = layout.round_record_bytes + (
        layout.moved_match_max_per_round * layout.moved_match_bytes
    )
    longest_block = (
        layout.body_offset
        + 2 * _UINT32.size
        + layout.tie_break_count_max
        + _UINT32.size * layout.prize_count_max
        + _UINT32.size
        + layout.round_count_max * longest_round
        - layout.promotion_quad_offset
    )
    return _RulesSearch(
        marker=layout.marker,
        promotion_quad_offset=layout.promotion_quad_offset,
        promotion_quad_bytes=layout.promotion_quad_bytes,
        body_offset=layout.body_offset,
        tie_break_count_max=layout.tie_break_count_max,
        prize_count_max=layout.prize_count_max,
        round_count_max=layout.round_count_max,
        round_record_bytes=layout.round_record_bytes,
        round_anchor_search_bytes=layout.round_anchor_search_bytes,
        round_kind_offset=layout.round_kind_offset,
        round_date_offset=layout.round_date_offset,
        round_b5_offset=layout.round_b5_offset,
        round_number_offset=layout.round_number_offset,
        round_match_count_offset=layout.round_match_count_offset,
        round_match_count_max=layout.round_match_count_max,
        round_ordinal_offset=layout.round_ordinal_offset,
        round_indexed_kind_value=layout.round_indexed_kind_value,
        moved_match_bytes=layout.moved_match_bytes,
        moved_match_sentinel_offset=layout.moved_match_sentinel_offset,
        moved_match_sentinel_value=layout.moved_match_sentinel_value,
        round_interstitial_tag_offset=layout.round_interstitial_tag_offset,
        round_interstitial_tag_value=layout.round_interstitial_tag_value,
        moved_match_tail_offset=layout.moved_match_tail_offset,
        moved_match_tail=layout.moved_match_tail,
        moved_match_max_per_round=layout.moved_match_max_per_round,
        search_back_bytes=longest_block,
    )


def _optional_id(value: int) -> int | None:
    return None if value == 0 or value == MISSING_REFERENCE else value


def _raw_fixture(values: tuple[Any, ...], absolute: int, search: _FixtureSearch) -> RawFixture:
    """Use the same stored-field conversion for strict anchors and counted continuations."""
    stored_stadium: int = values[search.stadium_ordinal_index]
    stadium_ordinal = None if _optional_id(stored_stadium) is None else stored_stadium - 1
    stage_id: int = values[search.stage_id_index]
    season_start_year: int = values[search.season_start_year_index]
    template: bytes = values[search.match_rules_template_index]
    return RawFixture(
        span_offset=absolute,
        stage_id=None if stage_id == MISSING_REFERENCE else stage_id,
        stadium_ordinal=stadium_ordinal,
        home_team_id=values[search.home_team_id_index],
        away_team_id=values[search.away_team_id_index],
        packed_kick_off=values[search.packed_kick_off_index],
        kick_off_year=values[search.kick_off_year_index],
        season_start_year=season_start_year or None,
        match_record_id=_optional_id(values[search.match_record_id_index]),
        round_index=values[search.round_index_index],
        played=values[search.played_index] != 0,
        date2=values[search.date2_index],
        phase=values[search.phase_index],
        leg=values[search.leg_index],
        r39_42=values[search.r39_42_index],
        match_rules_template=(template[0], template[1], template[2]),
        r47_54=values[search.r47_54_index],
    )


def _collect_fixtures(
    window: bytes,
    window_origin: int,
    search_from: int,
    search: _FixtureSearch,
    considered_to: int,
    fixtures: list[RawFixture],
) -> tuple[int, int]:
    """Append every accepted fixture record in the window; return (considered to, candidates)."""
    find_match = search.pattern.search
    window_length = len(window)
    match_offset = search.match_offset
    record_bytes = search.record_bytes
    marker_byte_offset = search.marker_byte_offset
    marker_byte_value = search.marker_byte_value
    sentinel_offsets = search.sentinel_offsets
    unpack_fields = search.fields_struct.unpack_from
    struct_start = search.struct_start
    home_team_id_index = search.home_team_id_index
    away_team_id_index = search.away_team_id_index
    lowest_team_id = search.lowest_team_id
    highest_team_id = search.highest_team_id
    add_fixture = fixtures.append
    candidates = 0

    match = find_match(window, search_from)
    while match is not None:
        match_start = match.start()
        match = find_match(window, match_start + 1)
        record_start = match_start - match_offset
        if record_start + marker_byte_offset < 0 or record_start + record_bytes > window_length:
            continue
        absolute = window_origin + record_start
        if absolute <= considered_to:
            continue
        considered_to = absolute
        candidates += 1
        if window[record_start + marker_byte_offset] != marker_byte_value:
            continue
        if any(window[record_start + offset] != value for offset, value in sentinel_offsets):
            continue
        values = unpack_fields(window, record_start + struct_start)
        home_team_id: int = values[home_team_id_index]
        away_team_id: int = values[away_team_id_index]
        if not (
            lowest_team_id <= home_team_id <= highest_team_id
            and lowest_team_id <= away_team_id <= highest_team_id
        ):
            continue
        add_fixture(_raw_fixture(values, absolute, search))
    return considered_to, candidates


@dataclass(slots=True)
class _FixtureContinuationState:
    """Incremental framing without retaining a decompressed frame or event payload."""

    left: int | None = None
    cursor: int = 0
    core: RawFixture | None = None
    pending: list[RawFixture] = field(default_factory=lambda: list[RawFixture]())
    next_score: tuple[int, int] | None = None
    pending_scores: list[RawFixtureScore] = field(default_factory=lambda: list[RawFixtureScore]())
    next_played: bool | None = None
    pending_presence: list[RawFixturePresence] = field(
        default_factory=lambda: list[RawFixturePresence]()
    )

    def reset(self, anchor: RawFixture | None = None) -> None:
        self.left = None if anchor is None else anchor.span_offset
        self.cursor = 0 if anchor is None else anchor.span_offset
        self.core = anchor
        self.pending.clear()
        self.next_score = None
        self.pending_scores.clear()
        self.next_played = None
        self.pending_presence.clear()

    def advance(
        self,
        window: bytes,
        origin: int,
        search: _FixtureSearch,
        layout: FixtureCalendarLayout,
        clock_year: int,
        stop: int | None,
    ) -> bool:
        while self.left is not None:
            if self.cursor - self.left > layout.cluster_gap_bytes:
                self.reset()
                return False
            if self.core is None and stop == self.cursor:
                at = self.cursor - origin
                if (
                    at < 0
                    or at + search.core_end > len(window)
                    or decode_date(window, at + layout.kick_off_date_offset) is None
                ):
                    self.reset()
                    return False
                self._keep_status(self.cursor)
                return True
            if stop is not None and self.cursor >= stop:
                self.reset()
                return False
            if self.core is not None:
                at = self.cursor + search.core_end - origin
                if at < 0:
                    self.reset()
                    return False
                if at >= len(window):
                    return False
                presence = window[at]
                if presence == 0:
                    self.next_played = False
                    self.next_score = None
                    self.cursor = origin + at + 1 - layout.marker_byte_offset
                    self.core = None
                    continue
                if presence != 1:
                    self.reset()
                    return False
                at += 1
                if at + layout.secondary_header_bytes > len(window):
                    return False
                if window[at] != layout.secondary_marker:
                    self.reset()
                    return False
                count = _UINT32.unpack_from(window, at + layout.secondary_count_offset)[0]
                self.next_played = True
                basic = (
                    window[at + layout.secondary_home_goals_offset],
                    window[at + layout.secondary_away_goals_offset],
                )
                optional = (
                    window[at + layout.secondary_optional_home_goals_offset],
                    window[at + layout.secondary_optional_away_goals_offset],
                )
                # These fields belong to the following core, not the preceding one.
                # The other packet bytes include shootout/aggregate-like values and
                # remain uninterpreted. Unsafe scores never invalidate framing.
                self.next_score = None
                if max(basic) <= layout.secondary_goals_maximum:
                    if optional == (layout.secondary_missing_goals,) * 2:
                        self.next_score = basic
                    elif (
                        max(optional) <= layout.secondary_goals_maximum
                        and optional[0] >= basic[0]
                        and optional[1] >= basic[1]
                    ):
                        self.next_score = optional
                # Event rows carry unidentified fields. Skip their declared byte extent
                # logically, even across many frames, without storing or interpreting it.
                self.cursor = (
                    origin
                    + at
                    + layout.secondary_header_bytes
                    + layout.secondary_item_bytes * count
                    - layout.marker_byte_offset
                )
                self.core = None
                continue
            at = self.cursor - origin
            if at + search.marker_byte_offset < 0:
                self.reset()
                return False
            # Wait for the strict scanner's existing admission extent. Otherwise a split
            # frame could consume a future strict endpoint as a provisional middle before
            # the strict scan sees it. Only the 67-byte core is actually unpacked below.
            if at + search.record_bytes > len(window):
                return False
            if (
                window[at + search.marker_byte_offset] != search.marker_byte_value
                or decode_date(window, at + layout.kick_off_date_offset) is None
            ):
                self.reset()
                return False
            values = search.core_struct.unpack_from(window, at + search.core_start)
            # The 67-byte core contains no current-record status. Insert the preceding
            # owned prefix, rather than reading the next row or collection as that value.
            assert self.next_played is not None
            values = (
                values[: search.played_index]
                + (int(self.next_played),)
                + values[search.played_index :]
            )
            self.core = _raw_fixture(values, self.cursor, search)
            self._keep_status(self.cursor)
            # Reference and output-year bounds do not decide where the owned path ends.
            # A filtered middle still supplies the next counted continuation.
            if (
                clock_year - layout.years_before_clock
                <= self.core.kick_off_year
                <= clock_year + layout.years_after_clock
                and search.lowest_team_id <= self.core.home_team_id <= search.highest_team_id
                and search.lowest_team_id <= self.core.away_team_id <= search.highest_team_id
            ):
                self.pending.append(self.core)
        return False

    def _keep_status(self, offset: int) -> None:
        assert self.next_played is not None
        self.pending_presence.append(RawFixturePresence(offset, self.next_played))
        if self.next_played:
            self.pending_scores.append(self._score(offset))

    def _score(self, offset: int) -> RawFixtureScore:
        home, away = self.next_score if self.next_score is not None else (None, None)
        return RawFixtureScore(offset, home, away)


@dataclass(slots=True)
class _FixtureCacheState:
    """An optional table-owned pair of counted lists, never a calendar search.

    Only scalar cursors and provisional offsets survive a frame. The raw vector,
    packet payloads and unidentified suffix words are skipped without interpreting
    them. Offsets become exclusions only after both lists and the next object prefix
    close. A rejected or truncated parent contributes nothing.
    """

    cursor: int
    limit: int
    phase: str = "vector"
    list_number: int = 0
    remaining: int = 0
    offsets: list[int] = field(default_factory=lambda: list[int]())

    def advance(
        self, window: bytes, origin: int, layout: FixtureCalendarLayout
    ) -> tuple[int, ...] | None:
        end = origin + len(window)
        home_at = -layout.marker_byte_offset
        while True:
            if self.phase == "vector":
                needed = layout.cache_vector_entries_offset
            elif self.phase == "dates":
                needed = len(layout.cache_dates_prefix) + 1
            elif self.phase in ("count", "date_count", "date"):
                needed = _UINT32.size
            elif self.phase == "packet":
                needed = layout.secondary_header_bytes
            elif self.phase == "core":
                needed = layout.cache_primary_bytes
            else:
                needed = len(layout.cache_next_prefix) + layout.cache_next_header_bytes
            if self.cursor < origin or self.cursor + needed > self.limit:
                return ()
            if self.cursor + needed > end:
                return None
            at = self.cursor - origin
            if self.phase == "vector":
                count = window[at + layout.cache_vector_count_offset]
                if any(
                    _UINT16.unpack_from(window, at + offset)[0] != count
                    for offset in layout.cache_vector_count_copy_offsets
                ):
                    return ()
                constant_at = at + layout.cache_vector_constant_offset
                if window[constant_at : constant_at + len(layout.cache_vector_constant)] != (
                    layout.cache_vector_constant
                ):
                    return ()
                self.cursor += layout.cache_vector_entries_offset + count
                self.phase = "dates"
            elif self.phase == "dates":
                prefix_end = at + len(layout.cache_dates_prefix)
                present = window[prefix_end]
                if window[at:prefix_end] != layout.cache_dates_prefix or present not in (0, 1):
                    return ()
                self.cursor += needed
                if present:
                    self.phase = "date_count"
                else:
                    self.cursor += layout.cache_vector_tail_bytes
                    self.phase = "count"
            elif self.phase == "date_count":
                self.remaining = _UINT32.unpack_from(window, at)[0]
                self.cursor += _UINT32.size
                if (
                    self.remaining * _UINT32.size + layout.cache_vector_tail_bytes
                    > self.limit - self.cursor
                ):
                    return ()
                if self.remaining:
                    self.phase = "date"
                else:
                    self.cursor += layout.cache_vector_tail_bytes
                    self.phase = "count"
            elif self.phase == "date":
                if decode_date(window, at) is None:
                    return ()
                self.cursor += _UINT32.size
                self.remaining -= 1
                if not self.remaining:
                    self.cursor += layout.cache_vector_tail_bytes
                    self.phase = "count"
            elif self.phase == "count":
                self.remaining = _UINT32.unpack_from(window, at)[0]
                self.cursor += _UINT32.size
                minimum_row = layout.secondary_header_bytes + layout.cache_primary_bytes
                if self.remaining * minimum_row > self.limit - self.cursor:
                    return ()
                if self.remaining:
                    self.phase = "packet"
                elif self.list_number == 0:
                    self.list_number = 1
                else:
                    self.phase = "next"
            elif self.phase == "packet":
                if window[at] != layout.secondary_marker:
                    return ()
                count = _UINT32.unpack_from(window, at + layout.secondary_count_offset)[0]
                self.cursor += layout.secondary_header_bytes + count * layout.secondary_item_bytes
                self.phase = "core"
            elif self.phase == "core":
                home = at + home_at
                suffix_at = home + layout.cache_primary_suffix_offset
                if (
                    window[at] != layout.marker_byte_value
                    or decode_date(window, home + layout.kick_off_date_offset) is None
                    or window[suffix_at : suffix_at + len(layout.cache_primary_suffix)]
                    != layout.cache_primary_suffix
                ):
                    return ()
                self.offsets.append(self.cursor + home_at)
                self.cursor += layout.cache_primary_bytes
                self.remaining -= 1
                if self.remaining:
                    self.phase = "packet"
                elif self.list_number == 0:
                    self.list_number = 1
                    self.phase = "count"
                else:
                    self.phase = "next"
            else:
                prefix_end = at + len(layout.cache_next_prefix)
                if window[at:prefix_end] != layout.cache_next_prefix:
                    return ()
                tag_at = prefix_end + layout.cache_next_tag_offset
                tag = window[tag_at : tag_at + layout.cache_next_tag_bytes]
                constant_at = prefix_end + layout.cache_next_constant_offset
                if (
                    any(not 32 <= byte <= 126 for byte in tag)
                    or window[constant_at : constant_at + len(layout.cache_next_constant)]
                    != layout.cache_next_constant
                ):
                    return ()
                return tuple(self.offsets)


def _collect_table_blocks(
    window: bytes,
    window_origin: int,
    search_from: int,
    search: _TableSearch,
    considered_to: int,
    table_blocks: list[RawTableBlock],
) -> tuple[int, int]:
    """Append every accepted league-table block; return (considered to, candidates)."""
    find_match = search.pattern.search
    window_length = len(window)
    row_bytes = search.row_bytes
    aggregate_count = search.aggregate_count
    team_id_offset = search.team_id_offset
    head_bytes_offset = search.head_bytes_offset
    head_bytes_count = search.head_bytes_count
    rounds_per_venue_offset = search.rounds_per_venue_offset
    matches_offset = search.matches_offset
    lowest_rounds_per_venue = search.lowest_rounds_per_venue
    highest_rounds_per_venue = search.highest_rounds_per_venue
    unpack_row = search.row_struct.unpack_from
    key_index = search.key_index
    played_index = search.played_index
    played_copy_index = search.played_copy_index
    won_index = search.won_index
    drawn_index = search.drawn_index
    lost_index = search.lost_index
    goals_for_index = search.goals_for_index
    goals_against_index = search.goals_against_index
    points_index = search.points_index
    flag_index = search.flag_index
    lowest_offset = search.lowest_offset
    unpack_rounds = _UINT16.unpack_from
    unpack_team_id = _UINT32.unpack_from
    add_block = table_blocks.append
    candidates = 0

    match = find_match(window, search_from)
    while match is not None:
        head = match.start()
        match = find_match(window, head + 1)
        if head + lowest_offset < 0:
            # The bytes in front of this head lie before the region, so it can never be read.
            continue
        if head + matches_offset > window_length:
            break
        rounds_per_venue: int = unpack_rounds(window, head + rounds_per_venue_offset)[0]
        in_range = lowest_rounds_per_venue <= rounds_per_venue <= highest_rounds_per_venue
        match_count = 2 * rounds_per_venue
        block_end = head + matches_offset + row_bytes * match_count
        if in_range and block_end > window_length:
            # Deferred, so the scan of this window stops here rather than moving on. A block
            # is variable length, so a later candidate can still be judged where this one
            # cannot, and judging it would advance the high-water mark past this head and
            # hide it from the next window for good. Everything before here has been judged,
            # and the next window's carry holds this block whole.
            break
        absolute = window_origin + head
        if absolute <= considered_to:
            continue
        considered_to = absolute
        candidates += 1
        if not in_range:
            continue
        # The aggregate rows reject almost every candidate the pattern finds, so they are
        # read and checked before the match rows, which outnumber them many times over.
        aggregate_rows = [
            unpack_row(window, head + row_bytes * row_number)
            for row_number in range(aggregate_count)
        ]
        total_played: int = aggregate_rows[0][played_index]
        if total_played == 0:
            continue
        if any(
            row[played_index] != row[played_copy_index]
            or row[played_index] != row[won_index] + row[drawn_index] + row[lost_index]
            for row in aggregate_rows
        ):
            continue
        if aggregate_rows[1][played_index] + aggregate_rows[2][played_index] != total_played:
            continue
        if aggregate_rows[3][played_index] + aggregate_rows[4][played_index] != total_played:
            continue
        # The match rows start at matches_offset, which the aggregates do not reach.
        match_rows = [
            unpack_row(window, head + matches_offset + row_bytes * slot)
            for slot in range(match_count)
        ]
        head_start = head + head_bytes_offset
        add_block(
            RawTableBlock(
                span_offset=absolute,
                team_id=unpack_team_id(window, head + team_id_offset)[0],
                head_bytes=tuple(window[head_start : head_start + head_bytes_count]),
                aggregates=tuple(
                    RawTableRow(
                        key=row[key_index],
                        played=row[played_index],
                        won=row[won_index],
                        drawn=row[drawn_index],
                        lost=row[lost_index],
                        goals_for=row[goals_for_index],
                        goals_against=row[goals_against_index],
                        points=row[points_index],
                        flag=row[flag_index],
                    )
                    for row in aggregate_rows
                ),
                rounds_per_venue=rounds_per_venue,
                matches=tuple(
                    RawTableRow(
                        key=row[key_index],
                        played=row[played_index],
                        won=row[won_index],
                        drawn=row[drawn_index],
                        lost=row[lost_index],
                        goals_for=row[goals_for_index],
                        goals_against=row[goals_against_index],
                        points=row[points_index],
                        flag=row[flag_index],
                    )
                    for row in match_rows
                ),
            )
        )
    return considered_to, candidates


def _rules_block(
    span_offset: int,
    quad: bytes | None,
    tie_breaks: tuple[int, ...],
    prize_money: tuple[int, ...],
    rounds: tuple[RawRulesRound, ...],
    *,
    fully_parsed: bool,
) -> RawRulesBlock:
    """One rules block; the four quad values are None together when the copies differed."""
    promotion_places = playoff_places = promotion_byte2 = relegation_places = None
    if quad is not None:
        promotion_places, playoff_places, promotion_byte2, relegation_places = quad
    return RawRulesBlock(
        span_offset=span_offset,
        promotion_places=promotion_places,
        playoff_places=playoff_places,
        promotion_byte2=promotion_byte2,
        relegation_places=relegation_places,
        tie_breaks=tie_breaks,
        prize_money=prize_money,
        rounds=rounds,
        fully_parsed=fully_parsed,
    )


def _parse_rules_block(
    window: bytes, span_offset: int, mark: int, search: _RulesSearch, *, final_window: bool = False
) -> RawRulesBlock | None:
    """The block at `mark`, or None when this window does not hold enough of it to judge.

    A list whose count is outside its bound, or a round record that does not decode, ends
    the parse and leaves the block not fully parsed; only bytes missing from the window
    return None, so that the next window, whose carry holds the block whole, judges it.
    The caller has already checked that the promotion quad lies inside the window, so None
    always means the block runs past the window's end and the scan of it must stop there.
    """
    window_length = len(window)
    quad_start = mark + search.promotion_quad_offset
    quad_bytes = search.promotion_quad_bytes
    first_copy = window[quad_start : quad_start + quad_bytes]
    second_copy = window[quad_start + quad_bytes : quad_start + 2 * quad_bytes]
    quad = first_copy if first_copy == second_copy else None
    no_rounds: tuple[RawRulesRound, ...] = ()

    cursor = mark + search.body_offset
    if cursor + _UINT32.size > window_length:
        return None
    tie_break_count: int = _UINT32.unpack_from(window, cursor)[0]
    if tie_break_count > search.tie_break_count_max:
        return _rules_block(span_offset, quad, (), (), no_rounds, fully_parsed=False)
    cursor += _UINT32.size
    if cursor + tie_break_count > window_length:
        return None
    tie_breaks = tuple(window[cursor : cursor + tie_break_count])
    cursor += tie_break_count

    if cursor + _UINT32.size > window_length:
        return None
    prize_count: int = _UINT32.unpack_from(window, cursor)[0]
    if prize_count > search.prize_count_max:
        return _rules_block(span_offset, quad, tie_breaks, (), no_rounds, fully_parsed=False)
    cursor += _UINT32.size
    if cursor + _UINT32.size * prize_count > window_length:
        return None
    prize_money = tuple(
        _UINT32.unpack_from(window, cursor + _UINT32.size * prize)[0]
        for prize in range(prize_count)
    )
    cursor += _UINT32.size * prize_count

    if cursor + _UINT32.size > window_length:
        return None
    round_count: int = _UINT32.unpack_from(window, cursor)[0]
    if not 0 < round_count <= search.round_count_max:
        return _rules_block(
            span_offset, quad, tie_breaks, prize_money, no_rounds, fully_parsed=False
        )
    rounds = _parse_rules_rounds(
        window, cursor + _UINT32.size, round_count, search, final_window=final_window
    )
    if rounds is None:
        return None
    return _rules_block(
        span_offset,
        quad,
        tie_breaks,
        prize_money,
        rounds,
        fully_parsed=quad is not None and len(rounds) == round_count,
    )


def _parse_rules_rounds(
    window: bytes,
    body_cursor: int,
    round_count: int,
    search: _RulesSearch,
    *,
    allow_tagged_interstitials: bool = False,
    require_indexed_calendar: bool = False,
    final_window: bool = False,
) -> tuple[RawRulesRound, ...] | None:
    """The block's round records, or None when the window does not hold them all.

    The list is anchored on the first offset after the round count whose date decodes, and
    the record starts one byte before it, because a round record opens with an unidentified
    byte which for the first record is the round count's own high byte. Between records the
    save writes interstitial entries, which are stepped over. The tagged variant has
    unidentified contents and is accepted only when every declared round can be read.
    A second complete walk requires the kind byte and parent ordinal on every row,
    allowing the unidentified u32 word to remain raw regardless of its magnitude.
    Structurally rejected variants preserve the original partial result; missing bytes
    defer judgment until another frame arrives. At EOF a final retry keeps the original
    prefix when a variant remains truncated.
    """
    window_length = len(window)
    record_bytes = search.round_record_bytes
    date_offset = search.round_date_offset
    match_count_offset = search.round_match_count_offset
    match_count_max = search.round_match_count_max
    number_offset = search.round_number_offset
    kind_offset = search.round_kind_offset
    b5_offset = search.round_b5_offset
    moved_match_bytes = search.moved_match_bytes
    moved_match_sentinel_offset = search.moved_match_sentinel_offset
    moved_match_sentinel_value = search.moved_match_sentinel_value
    moved_match_tail_offset = search.moved_match_tail_offset
    moved_match_tail = search.moved_match_tail
    moved_match_tail_end = moved_match_tail_offset + len(moved_match_tail)
    moved_match_max_per_round = search.moved_match_max_per_round

    position = -1
    for anchor in range(search.round_anchor_search_bytes):
        date_at = body_cursor + anchor
        if date_at + 4 > window_length:
            return None
        if decode_date(window, date_at) is not None:
            position = date_at - date_offset
            break
    if position < 0:
        return ()

    rounds: list[RawRulesRound] = []
    for round_number in range(round_count):
        if round_number:
            for _ in range(moved_match_max_per_round):
                if position + moved_match_bytes > window_length:
                    return None
                if (
                    window[position + moved_match_sentinel_offset] != moved_match_sentinel_value
                    and not (
                        allow_tagged_interstitials
                        and window[position + search.round_interstitial_tag_offset]
                        == search.round_interstitial_tag_value
                    )
                ) or window[
                    position + moved_match_tail_offset : position + moved_match_tail_end
                ] != moved_match_tail:
                    break
                position += moved_match_bytes
        if position + record_bytes > window_length:
            return None
        round_date = decode_date(window, position + date_offset)
        match_count: int = _UINT32.unpack_from(window, position + match_count_offset)[0]
        if round_date is None:
            break
        if require_indexed_calendar:
            if (
                window[position + kind_offset] != search.round_indexed_kind_value
                or window[position + search.round_ordinal_offset] != round_number
            ):
                break
        elif match_count > match_count_max:
            break
        rounds.append(
            RawRulesRound(
                number=window[position + number_offset] + 1,
                date=round_date,
                match_count=match_count,
                kind=window[position + kind_offset],
                b5=window[position + b5_offset],
            )
        )
        position += record_bytes
    if not allow_tagged_interstitials and len(rounds) < round_count:
        complete = _parse_rules_rounds(
            window,
            body_cursor,
            round_count,
            search,
            allow_tagged_interstitials=True,
            final_window=final_window,
        )
        if complete is None and not final_window:
            return None
        if complete is not None and len(complete) == round_count:
            return complete
        indexed = _parse_rules_rounds(
            window,
            body_cursor,
            round_count,
            search,
            allow_tagged_interstitials=True,
            require_indexed_calendar=True,
            final_window=final_window,
        )
        if indexed is None and not final_window:
            return None
        if indexed is not None and len(indexed) == round_count:
            return indexed
    return tuple(rounds)


def _collect_rules_blocks(
    window: bytes,
    window_origin: int,
    search_from: int,
    search: _RulesSearch,
    considered_to: int,
    rules_blocks: list[RawRulesBlock],
    *,
    final_window: bool = False,
) -> tuple[int, int]:
    """Append one block per rules marker judged here; return (considered to, markers)."""
    find_marker = window.find
    marker = search.marker
    promotion_quad_offset = search.promotion_quad_offset
    add_block = rules_blocks.append
    markers = 0

    position = find_marker(marker, search_from)
    while position >= 0:
        absolute = window_origin + position
        next_position = find_marker(marker, position + 1)
        # A marker whose quad lies before the region starts can never be read, so it is
        # passed over rather than deferred, which would stop the scan here for good.
        if absolute > considered_to and position + promotion_quad_offset >= 0:
            block = _parse_rules_block(
                window, absolute, position, search, final_window=final_window
            )
            if block is None:
                # Deferred, so the scan of this window stops here rather than moving on, for
                # the reason the league-table scan stops: a block is variable length, and a
                # later marker that can be judged would hide this one from the next window.
                break
            considered_to = absolute
            markers += 1
            add_block(block)
        position = next_position
    return considered_to, markers


def scan_span(
    frames: Iterable[bytes], layouts: SpanLayouts, clock: datetime.date, file_name: str
) -> SpanRecords:
    """Collect fixtures, table blocks, rules preambles and results from one pass over the span.

    `frames` are the region's decompressed frames in file order. Only one frame plus the
    carry-over is held at a time. A candidate that fails an acceptance check is not emitted
    and is never an error.

    Raises:
        CorruptSaveError: A decode ran past its window, which the acceptance checks should
            have caught, so the span is damaged or was being written.
        ValueError: A layout is inconsistent (see the `_*_search` builders).
    """
    fixture_search = _fixture_search(layouts.fixtures, clock.year)
    table_search = _table_search(layouts.tables)
    rules_search = _rules_search(layouts.rules)
    results_search = result_search(layouts.results)
    carry_over_bytes = layouts.carry_over_bytes

    fixtures: list[RawFixture] = []
    fixture_continuations: list[RawFixtureContinuation] = []
    fixture_scores: list[RawFixtureScore] = []
    fixture_presence: list[RawFixturePresence] = []
    fixture_cache_offsets: set[int] = set()
    cache_states: list[_FixtureCacheState] = []
    continuation = _FixtureContinuationState()
    if (
        layouts.fixtures.secondary_count_offset < 1
        or layouts.fixtures.secondary_count_offset + _UINT32.size
        > layouts.fixtures.secondary_header_bytes
        or layouts.fixtures.secondary_item_bytes <= 0
        or layouts.fixtures.secondary_header_bytes > carry_over_bytes
        or fixture_search.record_bytes - fixture_search.marker_byte_offset > carry_over_bytes
    ):
        raise ValueError("fixture continuation headers must fit the streamed carry")
    score_offsets = (
        layouts.fixtures.secondary_home_goals_offset,
        layouts.fixtures.secondary_away_goals_offset,
        layouts.fixtures.secondary_optional_home_goals_offset,
        layouts.fixtures.secondary_optional_away_goals_offset,
    )
    if (
        len(set(score_offsets)) != len(score_offsets)
        or any(
            not 1 <= offset < layouts.fixtures.secondary_count_offset for offset in score_offsets
        )
        or not 0
        <= layouts.fixtures.secondary_goals_maximum
        < layouts.fixtures.secondary_missing_goals
        or layouts.fixtures.secondary_missing_goals > 255
    ):
        raise ValueError("fixture score fields must fit the secondary header")
    cache_layout = layouts.fixtures
    home_at = -cache_layout.marker_byte_offset
    if (
        not 0 <= cache_layout.cache_vector_count_offset < cache_layout.cache_vector_entries_offset
        or any(
            not 0 <= offset <= cache_layout.cache_vector_entries_offset - _UINT16.size
            for offset in cache_layout.cache_vector_count_copy_offsets
        )
        or not 0
        <= cache_layout.cache_vector_constant_offset
        <= cache_layout.cache_vector_entries_offset - len(cache_layout.cache_vector_constant)
        or cache_layout.cache_vector_tail_bytes < 0
        or home_at < 0
        or home_at + cache_layout.kick_off_date_offset < 0
        or home_at + cache_layout.kick_off_date_offset + 4 > cache_layout.cache_primary_bytes
        or home_at + cache_layout.cache_primary_suffix_offset < 0
        or home_at
        + cache_layout.cache_primary_suffix_offset
        + len(cache_layout.cache_primary_suffix)
        > cache_layout.cache_primary_bytes
        or not 0
        <= cache_layout.cache_next_tag_offset
        <= cache_layout.cache_next_header_bytes - cache_layout.cache_next_tag_bytes
        or not 0
        <= cache_layout.cache_next_constant_offset
        <= cache_layout.cache_next_header_bytes - len(cache_layout.cache_next_constant)
        or max(
            cache_layout.cache_vector_entries_offset,
            len(cache_layout.cache_dates_prefix) + 1,
            cache_layout.cache_primary_bytes,
            len(cache_layout.cache_next_prefix) + cache_layout.cache_next_header_bytes,
        )
        > carry_over_bytes
    ):
        raise ValueError("fixture cache fields must fit their owned streamed headers")
    table_blocks: list[RawTableBlock] = []
    rules_blocks: list[RawRulesBlock] = []
    results: list[RawStageResult] = []
    fixture_candidates = 0
    table_block_candidates = 0
    rules_markers = 0
    result_candidates = 0
    fixtures_considered_to = -1
    tables_considered_to = -1
    rules_considered_to = -1
    results_considered_to = -1

    carry = b""
    window_origin = 0
    span_bytes = 0
    frame_count = 0
    for frame_bytes in frames:
        window = carry + frame_bytes if carry else frame_bytes
        carry_length = len(window) - len(frame_bytes)
        frame_count += 1
        span_bytes += len(frame_bytes)
        try:
            first_new_fixture = len(fixtures)
            fixtures_considered_to, found_fixtures = _collect_fixtures(
                window,
                window_origin,
                max(0, carry_length - fixture_search.search_back_bytes),
                fixture_search,
                fixtures_considered_to,
                fixtures,
            )
            for anchor in fixtures[first_new_fixture:]:
                closed = continuation.advance(
                    window,
                    window_origin,
                    fixture_search,
                    layouts.fixtures,
                    clock.year,
                    anchor.span_offset,
                )
                if closed and continuation.pending and continuation.left is not None:
                    fixture_continuations.append(
                        RawFixtureContinuation(
                            continuation.left,
                            anchor.span_offset,
                            tuple(continuation.pending),
                        )
                    )
                if closed:
                    fixture_scores.extend(continuation.pending_scores)
                    fixture_presence.extend(continuation.pending_presence)
                continuation.reset(anchor)
            # Advance on every frame, including frames without a new strict anchor. Only
            # fixed-header scalars and provisional decoded rows survive the next frame.
            continuation.advance(
                window,
                window_origin,
                fixture_search,
                layouts.fixtures,
                clock.year,
                None,
            )
            first_new_table = len(table_blocks)
            tables_considered_to, found_blocks = _collect_table_blocks(
                window,
                window_origin,
                max(0, carry_length - table_search.search_back_bytes),
                table_search,
                tables_considered_to,
                table_blocks,
            )
            for block in table_blocks[first_new_table:]:
                block_end = (
                    block.span_offset
                    + layouts.tables.matches_offset
                    + layouts.tables.row_bytes * 2 * block.rounds_per_venue
                )
                cache_states.append(
                    _FixtureCacheState(block_end, block_end + cache_layout.cluster_gap_bytes)
                )
            pending_caches: list[_FixtureCacheState] = []
            for cache in cache_states:
                offsets = cache.advance(window, window_origin, cache_layout)
                if offsets is None:
                    pending_caches.append(cache)
                else:
                    fixture_cache_offsets.update(offsets)
            cache_states = pending_caches
            rules_considered_to, found_markers = _collect_rules_blocks(
                window,
                window_origin,
                max(0, carry_length - rules_search.search_back_bytes),
                rules_search,
                rules_considered_to,
                rules_blocks,
            )
            results_considered_to, found_results = collect_results(
                window,
                window_origin,
                max(0, carry_length - results_search.search_back_bytes),
                results_search,
                results_considered_to,
                results,
            )
        except (struct.error, IndexError, CorruptSaveError) as error:
            raise _span_decode_error(file_name, error) from error
        fixture_candidates += found_fixtures
        table_block_candidates += found_blocks
        rules_markers += found_markers
        result_candidates += found_results

        window_end = window_origin + len(window)
        carry = window[-carry_over_bytes:] if len(window) > carry_over_bytes else window
        window_origin = window_end - len(carry)
    # A complete-calendar retry may have needed bytes beyond the last frame. Judge only
    # deferred rules markers once more at EOF, retaining their original partial prefix.
    # The existing carry exceeds the longest bounded rules block; no extra buffer is kept.
    try:
        _, final_markers = _collect_rules_blocks(
            carry,
            window_origin,
            0,
            rules_search,
            rules_considered_to,
            rules_blocks,
            final_window=True,
        )
    except (struct.error, IndexError, CorruptSaveError) as error:
        raise _span_decode_error(file_name, error) from error
    rules_markers += final_markers
    return SpanRecords(
        fixtures=tuple(fixtures),
        table_blocks=tuple(table_blocks),
        rules_blocks=tuple(rules_blocks),
        results=tuple(results),
        fixture_candidates=fixture_candidates,
        table_block_candidates=table_block_candidates,
        rules_markers=rules_markers,
        result_candidates=result_candidates,
        span_bytes=span_bytes,
        frame_count=frame_count,
        fixture_continuations=tuple(fixture_continuations),
        fixture_scores=tuple(fixture_scores),
        fixture_presence=tuple(fixture_presence),
        fixture_cache_offsets=tuple(sorted(fixture_cache_offsets)),
    )
