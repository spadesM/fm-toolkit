"""Stage results, owned match summaries and framed calendar scores.

A fixture record carries no score, so the goals of a finished match come from a separate
27-byte record that names the match by its date and its two team ids. Those records sit in the
unnamed span and in four named sections, and one locator reads them in all five, so the record
shape is written down once.

**The join is the evidence, not the locator.** A 27-byte shape with two short locator bytes
matches by chance many times over in a hundred megabytes, and acceptance turns away almost
nothing on its own. What says these records are matches is that they join the fixture calendar,
which another reader found in another region under an entirely different locator, on the date
and both team ids at once. Joined with the two sides swapped, or with the date moved a single
day, the same records join nothing at all.

Scope is decided in two steps, because the records are collected before the calendar exists.
The span pass runs first and can only apply the tests the record answers by itself: the locator
bytes, the team range, the goal ceiling and a date that decodes. Whether a record is in scope
needs the fixture calendar and the stage table, so one predicate, `result_in_scope`, is applied
afterwards to the span's records and the sections' records alike. Neither path has an acceptance
rule of its own.

The acceptance window is the calendar's own first and last date. A record dated outside the
range the calendar covers can never join a fixture, whatever is done with it: a save keeps
several seasons of history these records describe and no fixture survives to carry it, so those
records are dropped for want of somewhere to put them, not because they are wrong.

Stage-result retention is partial. Counted owned summaries provide another score source,
joined by exact date, competition and both teams after stage results are applied. They fill
only missing complete scores for uniquely matched played fixtures; existing scores and
stage-result contradictions remain authoritative. A played fixture with empty goals is an
unresolved result, not a goalless match.

Counted packets between calendar records carry scores for the following physical record.
The span pass retains them only after exact path closure. They can fill missing played
scores even when date/team keys are duplicated, without choosing between those copies.
Existing scores, stage contradictions and poisoned summary keys remain authoritative.
"""

from __future__ import annotations

import datetime
import functools
import re
import struct
from collections.abc import Container, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import StageResultLayout, find_layout
from fm26save._core._reader_stats import ResultStats
from fm26save._core._scan import decode_date
from fm26save._core.models.fixtures import Fixture
from fm26save._core.readers._common import SPAN_REGION, build_gap_padded_struct
from fm26save._core.readers.match_summaries import MatchSummaryScores

_UINT16 = struct.Struct("<H")

# The key "result_r22" of `Fixture.unknown`, which only a scored fixture carries.
RESULT_UNKNOWN_KEY = "result_r22"


@dataclass(frozen=True, slots=True)
class RawStageResult:
    """One stage-keyed result record, as stored.

    The date is decoded here because the locator has to decode it anyway to accept the record,
    and the goals are the two bytes as stored. `r22` is the first of the five unidentified
    bytes that follow the score, which reaches `Fixture.unknown` unchanged.
    """

    date: datetime.date
    stage_id: int
    home_team_id: int
    away_team_id: int
    home_goals: int
    away_goals: int
    r22: int


@dataclass(frozen=True, slots=True)
class LocatedResults:
    """The in-scope records one section yielded, and every candidate the locator judged.

    `candidates` counts what was judged rather than what was kept, so a gate on an accept rate
    has its denominator without walking the section a second time.
    """

    results: tuple[RawStageResult, ...]
    candidates: int


@dataclass(frozen=True, slots=True)
class ResultSearch:
    """Everything the result scan needs from a `StageResultLayout`, derived once."""

    pattern: re.Pattern[bytes]
    match_offset: int
    record_bytes: int
    lead_byte_offset: int
    lead_byte_value: int
    date_offset: int
    fields_struct: struct.Struct
    stage_id_index: int
    home_team_id_index: int
    away_team_id_index: int
    home_goals_offset: int
    away_goals_offset: int
    r22_offset: int
    lowest_team_id: int
    highest_team_id: int
    goals_maximum: int
    search_back_bytes: int


def find_result_layout(build: str) -> StageResultLayout:
    """Look up the stage-keyed result layout for a build. The span carries no schema number."""
    return find_layout(StageResultLayout, SPAN_REGION, None, build).layout


@functools.cache
def result_search(layout: StageResultLayout) -> ResultSearch:
    """The result pattern and struct for one layout, built on first use.

    The pattern anchors on the two-byte sentinel and runs to the zero byte the locator
    requires, which gives the regex engine a far more selective literal than the single lead
    byte would; the lead byte is checked separately once a candidate has been placed.

    Raises:
        ValueError: A field starts before the record or ends past it, the sentinel and the zero
            byte overlap, or two fields overlap.
    """
    single_byte_offsets = (
        layout.lead_byte_offset,
        layout.zero_byte_offset,
        layout.home_goals_offset,
        layout.away_goals_offset,
        layout.r22_offset,
    )
    word_offsets = (
        layout.date_offset,
        layout.stage_id_offset,
        layout.home_team_id_offset,
        layout.away_team_id_offset,
    )
    for offset in single_byte_offsets:
        if not 0 <= offset < layout.record_bytes:
            raise ValueError(
                f"the byte at offset {offset} lies outside the {layout.record_bytes}-byte "
                "result record"
            )
    for offset in word_offsets:
        if offset < 0 or offset + 4 > layout.record_bytes:
            raise ValueError(
                f"the word at offset {offset} lies outside the {layout.record_bytes}-byte "
                "result record"
            )
    if not 0 <= layout.sentinel_offset:
        raise ValueError("the sentinel must start at or after the record start")
    if layout.sentinel_offset + _UINT16.size > layout.zero_byte_offset:
        raise ValueError(
            f"the sentinel at offset {layout.sentinel_offset} runs into the zero byte at "
            f"offset {layout.zero_byte_offset}, so no single pattern spans them"
        )
    filler_bytes = layout.zero_byte_offset - layout.sentinel_offset - _UINT16.size
    pattern = re.compile(
        re.escape(_UINT16.pack(layout.sentinel_value)) + b".{%d}" % filler_bytes + b"\x00",
        re.DOTALL,
    )
    fields_struct, _struct_start, index_by_name = build_gap_padded_struct(
        [
            (layout.stage_id_offset, "I", "stage_id"),
            (layout.home_team_id_offset, "I", "home_team_id"),
            (layout.away_team_id_offset, "I", "away_team_id"),
        ],
        start_offset=0,
    )
    lowest_team_id, highest_team_id = layout.team_id_range
    return ResultSearch(
        pattern=pattern,
        match_offset=layout.sentinel_offset,
        record_bytes=layout.record_bytes,
        lead_byte_offset=layout.lead_byte_offset,
        lead_byte_value=layout.lead_byte_value,
        date_offset=layout.date_offset,
        fields_struct=fields_struct,
        stage_id_index=index_by_name["stage_id"],
        home_team_id_index=index_by_name["home_team_id"],
        away_team_id_index=index_by_name["away_team_id"],
        home_goals_offset=layout.home_goals_offset,
        away_goals_offset=layout.away_goals_offset,
        r22_offset=layout.r22_offset,
        lowest_team_id=lowest_team_id,
        highest_team_id=highest_team_id,
        goals_maximum=layout.goals_maximum,
        search_back_bytes=layout.record_bytes,
    )


def collect_results(
    window: bytes,
    window_origin: int,
    search_from: int,
    search: ResultSearch,
    considered_to: int,
    results: list[RawStageResult],
) -> tuple[int, int]:
    """Append every structurally sound result record in the window; return (considered to,
    candidates).

    Only the tests a record answers by itself are applied here, because this runs during the
    span pass, before the fixture calendar or the stage table exists. `result_in_scope` is what
    decides the rest, and it is applied to what this collects wherever it is called from.

    A result record is a fixed length, so no later record can fit where an earlier one does not
    and the scan runs to the end of the window rather than stopping at the first record that
    does not fit.
    """
    find_match = search.pattern.search
    window_length = len(window)
    match_offset = search.match_offset
    record_bytes = search.record_bytes
    lead_byte_offset = search.lead_byte_offset
    lead_byte_value = search.lead_byte_value
    date_offset = search.date_offset
    unpack_fields = search.fields_struct.unpack_from
    stage_id_index = search.stage_id_index
    home_team_id_index = search.home_team_id_index
    away_team_id_index = search.away_team_id_index
    home_goals_offset = search.home_goals_offset
    away_goals_offset = search.away_goals_offset
    r22_offset = search.r22_offset
    lowest_team_id = search.lowest_team_id
    highest_team_id = search.highest_team_id
    goals_maximum = search.goals_maximum
    add_result = results.append
    candidates = 0

    match = find_match(window, search_from)
    while match is not None:
        match_start = match.start()
        match = find_match(window, match_start + 1)
        record_start = match_start - match_offset
        if record_start < 0 or record_start + record_bytes > window_length:
            continue
        absolute = window_origin + record_start
        if absolute <= considered_to:
            continue
        considered_to = absolute
        candidates += 1
        if window[record_start + lead_byte_offset] != lead_byte_value:
            continue
        values = unpack_fields(window, record_start)
        home_team_id: int = values[home_team_id_index]
        away_team_id: int = values[away_team_id_index]
        if not (
            lowest_team_id <= home_team_id <= highest_team_id
            and lowest_team_id <= away_team_id <= highest_team_id
        ):
            continue
        home_goals = window[record_start + home_goals_offset]
        away_goals = window[record_start + away_goals_offset]
        if home_goals > goals_maximum or away_goals > goals_maximum:
            continue
        match_date = decode_date(window, record_start + date_offset)
        if match_date is None:
            continue
        add_result(
            RawStageResult(
                date=match_date,
                stage_id=values[stage_id_index],
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_goals=home_goals,
                away_goals=away_goals,
                r22=window[record_start + r22_offset],
            )
        )
    return considered_to, candidates


def result_in_scope(
    raw_result: RawStageResult,
    stage_ids: Container[int],
    earliest_date: datetime.date,
    latest_date: datetime.date,
) -> bool:
    """Whether a record could name a match this calendar holds.

    This is the one acceptance rule the span's records and the sections' records are both
    judged by, so neither route can drift into accepting what the other would not. Both tests
    need a reader that has already run: the stage table for the ids, and the calendar for the
    dates it covers.
    """
    return earliest_date <= raw_result.date <= latest_date and raw_result.stage_id in stage_ids


def locate_stage_results(
    section_bytes: bytes,
    layout: StageResultLayout,
    stage_ids: Container[int],
    earliest_date: datetime.date,
    latest_date: datetime.date,
) -> LocatedResults:
    """Every in-scope result record in one section's bytes, and the candidates judged.

    The section is already held whole by its caller's borrow, so it is scanned as one window.
    """
    search = result_search(layout)
    found: list[RawStageResult] = []
    _considered_to, candidates = collect_results(section_bytes, 0, 0, search, -1, found)
    return LocatedResults(
        results=tuple(
            raw_result
            for raw_result in found
            if result_in_scope(raw_result, stage_ids, earliest_date, latest_date)
        ),
        candidates=candidates,
    )


def calendar_dates(fixtures: Sequence[Fixture]) -> tuple[datetime.date, datetime.date] | None:
    """The calendar's own first and last fixture date, or None when it holds no dated match.

    This is the window result records are accepted in, so it comes from the calendar itself
    rather than from a constant: a record dated outside it has no fixture that could match.
    """
    dates = [fixture.date for fixture in fixtures if fixture.date is not None]
    if not dates:
        return None
    return min(dates), max(dates)


def apply_results(
    fixtures: Sequence[Fixture],
    results: Iterable[RawStageResult],
    *,
    candidates: int,
    summaries: MatchSummaryScores | None = None,
    packet_scores: Mapping[int, tuple[int, int] | None] | None = None,
) -> tuple[tuple[Fixture, ...], ResultStats]:
    """Join the results onto the calendar and return new fixtures carrying their scores.

    Fixtures are frozen, so a scored match becomes a new record and every other one is handed
    back unchanged.

    A record that matches no fixture is counted and dropped. A record matching more than one
    fixture fills neither, because attributing a score by a guess is a guessed value. A fixture
    the calendar does not mark played never receives a score.

    The same match is stored about 1.8 times over, so the first copy of a score wins and a later
    copy carrying the same score is ordinary rather than an anomaly. A later copy carrying a
    *different* score is a contradiction that arrival order must not settle: it counts a
    disagreement and leaves that fixture with no score at all, and no third copy can revive it.

    That contradiction test is on the goals alone. Two copies agreeing on the score and
    differing in `r22` are not treated as disagreeing: the first copy's `r22` is kept, which
    arrival order decides, and nothing counts it. Calling that a disagreement would be claiming
    to know what a byte whose meaning is unidentified ought to hold.

    Owned calendar packets fill only their exact physical fixture positions after the other
    sources, with the same existing-score and contradiction exclusions.

    Owned summaries can fill remaining played fixtures using their date, competition and
    both team ids. Their lookup already blocks conflicting or invalid score pairs. They never
    overwrite a score, fill a partial score, or revive a stage-result contradiction.
    """
    # Physical packet scores apply last so no independent source can revive a poisoned result.
    positions_by_key: dict[tuple[datetime.date, int, int], list[int]] = {}
    played_fixtures = 0
    for position, fixture in enumerate(fixtures):
        if fixture.played:
            played_fixtures += 1
        if fixture.date is None:
            continue
        key = (fixture.date, fixture.home_team_id, fixture.away_team_id)
        positions_by_key.setdefault(key, []).append(position)

    scores_by_position: dict[int, tuple[int, int, int]] = {}
    contradicted_positions: set[int] = set()
    accepted = 0
    joined = 0
    unjoined = 0
    ambiguous = 0
    score_for_unplayed = 0
    score_disagreements = 0
    for raw_result in results:
        accepted += 1
        positions = positions_by_key.get(
            (raw_result.date, raw_result.home_team_id, raw_result.away_team_id)
        )
        if positions is None:
            unjoined += 1
            continue
        joined += 1
        if len(positions) > 1:
            ambiguous += 1
            continue
        position = positions[0]
        if not fixtures[position].played:
            score_for_unplayed += 1
            continue
        if position in contradicted_positions:
            continue
        written = scores_by_position.get(position)
        if written is None:
            scores_by_position[position] = (
                raw_result.home_goals,
                raw_result.away_goals,
                raw_result.r22,
            )
            continue
        if written[0] != raw_result.home_goals or written[1] != raw_result.away_goals:
            score_disagreements += 1
            contradicted_positions.add(position)
            del scores_by_position[position]

    scored_fixtures: list[Fixture] = []
    for position, fixture in enumerate(fixtures):
        score = scores_by_position.get(position)
        if score is None:
            scored_fixtures.append(fixture)
            continue
        home_goals, away_goals, r22 = score
        scored_fixtures.append(
            replace(
                fixture,
                home_goals=home_goals,
                away_goals=away_goals,
                unknown=FrozenMapping({**fixture.unknown, RESULT_UNKNOWN_KEY: r22}),
            )
        )
    summary_unjoined = 0
    summary_ambiguous = 0
    summary_for_unplayed = 0
    summary_unsafe_keys = 0
    summary_existing_disagreements = 0
    summary_stage_conflicts = 0
    summary_scored_fixtures = 0
    if summaries is not None:
        summary_positions: dict[tuple[datetime.date, int, int, int], list[int]] = {}
        for position, fixture in enumerate(scored_fixtures):
            if fixture.date is not None and fixture.competition_id is not None:
                key = (
                    fixture.date,
                    fixture.competition_id,
                    fixture.home_team_id,
                    fixture.away_team_id,
                )
                summary_positions.setdefault(key, []).append(position)
        for key, summary_score in summaries.scores.items():
            if summary_score is None:
                summary_unsafe_keys += 1
                continue
            positions = summary_positions.get(key)
            if positions is None:
                summary_unjoined += 1
                continue
            if len(positions) != 1:
                summary_ambiguous += 1
                continue
            position = positions[0]
            fixture = scored_fixtures[position]
            if not fixture.played:
                summary_for_unplayed += 1
                continue
            if position in contradicted_positions:
                summary_stage_conflicts += 1
                continue
            known_score = (fixture.home_goals, fixture.away_goals)
            if any(goal is not None for goal in known_score):
                if any(
                    goal is not None and goal != summary_score[side]
                    for side, goal in enumerate(known_score)
                ):
                    summary_existing_disagreements += 1
                continue
            scored_fixtures[position] = replace(
                fixture, home_goals=summary_score[0], away_goals=summary_score[1]
            )
            summary_scored_fixtures += 1
    packet_unsafe_scores = 0
    packet_for_unplayed = 0
    packet_stage_conflicts = 0
    packet_summary_conflicts = 0
    packet_existing_disagreements = 0
    packet_scored_fixtures = 0
    if packet_scores is not None:
        for position, packet_score in packet_scores.items():
            if not 0 <= position < len(scored_fixtures):
                raise ValueError("packet score position lies outside the fixture calendar")
            if packet_score is None:
                packet_unsafe_scores += 1
                continue
            fixture = scored_fixtures[position]
            if not fixture.played:
                packet_for_unplayed += 1
                continue
            if position in contradicted_positions:
                packet_stage_conflicts += 1
                continue
            if (
                summaries is not None
                and fixture.date is not None
                and fixture.competition_id is not None
            ):
                summary_key = (
                    fixture.date,
                    fixture.competition_id,
                    fixture.home_team_id,
                    fixture.away_team_id,
                )
                if summary_key in summaries.scores and summaries.scores[summary_key] is None:
                    packet_summary_conflicts += 1
                    continue
            known_score = (fixture.home_goals, fixture.away_goals)
            if any(goal is not None for goal in known_score):
                if any(
                    goal is not None and goal != packet_score[side]
                    for side, goal in enumerate(known_score)
                ):
                    packet_existing_disagreements += 1
                continue
            scored_fixtures[position] = replace(
                fixture, home_goals=packet_score[0], away_goals=packet_score[1]
            )
            packet_scored_fixtures += 1
    stats = ResultStats(
        candidates=candidates,
        accepted=accepted,
        joined=joined,
        unjoined=unjoined,
        ambiguous=ambiguous,
        score_for_unplayed=score_for_unplayed,
        score_disagreements=score_disagreements,
        played_fixtures=played_fixtures,
        scored_fixtures=sum(
            fixture.home_goals is not None and fixture.away_goals is not None
            for fixture in scored_fixtures
        ),
        summary_lists_found=summaries.lists_found if summaries is not None else 0,
        summary_lists_decoded=summaries.lists_decoded if summaries is not None else 0,
        summary_records=summaries.record_count if summaries is not None else 0,
        summary_invalid_scores=summaries.invalid_score_records if summaries is not None else 0,
        summary_unjoined=summary_unjoined,
        summary_ambiguous=summary_ambiguous,
        summary_for_unplayed=summary_for_unplayed,
        summary_unsafe_keys=summary_unsafe_keys,
        summary_existing_disagreements=summary_existing_disagreements,
        summary_stage_conflicts=summary_stage_conflicts,
        summary_scored_fixtures=summary_scored_fixtures,
        packet_score_records=len(packet_scores) if packet_scores is not None else 0,
        packet_unsafe_scores=packet_unsafe_scores,
        packet_for_unplayed=packet_for_unplayed,
        packet_stage_conflicts=packet_stage_conflicts,
        packet_summary_conflicts=packet_summary_conflicts,
        packet_existing_disagreements=packet_existing_disagreements,
        packet_scored_fixtures=packet_scored_fixtures,
    )
    return tuple(scored_fixtures), stats
