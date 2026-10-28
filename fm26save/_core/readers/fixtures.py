"""The fixture calendar, built from the raw records one span pass collected.

The span holds several runs of fixture records: the career's own calendar, and stray copies
of it. One of those strays is a fixed block of template records dated years before the save's
clock and present with the same count on every save seen, so keeping it would put the same
phantom matches on every career. The runs are told apart by the distance between consecutive
records: a gap of `cluster_gap_bytes` or more starts a new one, and only the run holding the
most records is the calendar.

File order is neither sorted nor a rotation of a sorted order, so the kept run is sorted here
rather than trusted: the corpus shows dozens of places where a record's date is earlier than
the one before it. The sort is total, so successive saves of one career always list their
matches in the same order.

Dropping a run is not free, so what it costs is counted rather than left silent: most stray
records repeat a match the kept run already lists, and the count of those that do not is the
part of the drop that loses something.

Every join goes through an index another reader already built, and an id that does not
resolve leaves its fields empty and is counted rather than guessed.
"""

from __future__ import annotations

import datetime
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import FixtureCalendarLayout
from fm26save._core._reader_stats import FixtureStats
from fm26save._core._scan import TIME_SLOT_SHIFT, decode_date
from fm26save._core.models.clubs import Club
from fm26save._core.models.fixtures import Fixture
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.competitions import CompetitionIndex
from fm26save._core.readers.span import RawFixture, SpanRecords
from fm26save._core.readers.stadiums import StadiumIndex
from fm26save._core.readers.stages import StageIndex

# The kick-off date's two stored words, packed back together so the one date decoder in
# `_scan` reads them, rather than repeating its year and leap-year arithmetic here.
_DATE_WORDS = struct.Struct("<HH")
_MINUTES_PER_HOUR = 60
_MINUTES_PER_DAY = 24 * _MINUTES_PER_HOUR
_NO_CLUB: tuple[int | None, str | None, str | None, int | None] = (None, None, None, None)


def kick_off_time_of(packed_kick_off: int, layout: FixtureCalendarLayout) -> datetime.time | None:
    """The time of day a record's kick-off slot stands for, or None when it lands past midnight.

    The slot sits in the high bits of the packed kick-off date, and each step is
    `kick_off_slot_minutes` long counting from `kick_off_slot_offset` steps after midnight. A
    slot whose minutes reach a whole day names no time of day, so it reads as None.
    """
    slot = packed_kick_off >> TIME_SLOT_SHIFT
    minutes = (slot + layout.kick_off_slot_offset) * layout.kick_off_slot_minutes
    if not 0 <= minutes < _MINUTES_PER_DAY:
        return None
    return datetime.time(minutes // _MINUTES_PER_HOUR, minutes % _MINUTES_PER_HOUR)


def _cluster_bounds(
    raw_fixtures: Sequence[RawFixture], cluster_gap_bytes: int
) -> list[tuple[int, int]]:
    """The (start, stop) index range of each run of records, in span order."""
    if not raw_fixtures:
        return []
    bounds: list[tuple[int, int]] = []
    run_start = 0
    previous_offset = raw_fixtures[0].span_offset
    for position in range(1, len(raw_fixtures)):
        span_offset = raw_fixtures[position].span_offset
        if span_offset - previous_offset > cluster_gap_bytes:
            bounds.append((run_start, position))
            run_start = position
        previous_offset = span_offset
    bounds.append((run_start, len(raw_fixtures)))
    return bounds


@dataclass(frozen=True, slots=True)
class _SplitSpan:
    """The span's fixture records split into the calendar, the strays, and how many runs."""

    kept: tuple[RawFixture, ...]
    strays: tuple[RawFixture, ...]
    clusters: int


def _split_span(
    raw_fixtures: Sequence[RawFixture],
    cluster_gap_bytes: int,
    excluded_offsets: frozenset[int] = frozenset(),
) -> _SplitSpan:
    """Split the records into the calendar and everything else, walking the runs once.

    Records are split into runs wherever the distance between one record and the next is more
    than `cluster_gap_bytes`, and the run holding the most of them is the calendar. Two runs
    of the same length leave the earlier one, so the result never depends on which of them the
    span happened to hold first. The kept run, the records outside it and the number of runs
    all come from the one walk, so a hundred thousand records are never paced twice.
    """
    bounds = _cluster_bounds(raw_fixtures, cluster_gap_bytes)
    if not bounds:
        return _SplitSpan((), (), 0)
    if excluded_offsets:
        # A cache can occupy bytes between calendar records without belonging to
        # their calendar. Retain the original physical runs, but let only eligible
        # anchors vote for a run or appear in its output.
        runs = [
            tuple(
                record
                for record in raw_fixtures[start:stop]
                if record.span_offset not in excluded_offsets
            )
            for start, stop in bounds
        ]
        runs = [run for run in runs if run]
        if not runs:
            return _SplitSpan((), (), 0)
        selected = max(range(len(runs)), key=lambda index: len(runs[index]))
        return _SplitSpan(
            runs[selected],
            tuple(record for index, run in enumerate(runs) if index != selected for record in run),
            len(runs),
        )
    run_start, run_stop = max(bounds, key=lambda bound: bound[1] - bound[0])
    return _SplitSpan(
        tuple(raw_fixtures[run_start:run_stop]),
        (*raw_fixtures[:run_start], *raw_fixtures[run_stop:]),
        len(bounds),
    )


def largest_cluster(
    raw_fixtures: Sequence[RawFixture], cluster_gap_bytes: int
) -> tuple[RawFixture, ...]:
    """The run of records holding the most of them, which is the career's own calendar."""
    return _split_span(raw_fixtures, cluster_gap_bytes).kept


def _duplicate_key(raw_fixture: RawFixture) -> tuple[int, int, int, int]:
    """What makes one record a copy of another: both teams and the two kick-off words."""
    return (
        raw_fixture.home_team_id,
        raw_fixture.away_team_id,
        raw_fixture.packed_kick_off,
        raw_fixture.kick_off_year,
    )


def _strays_without_a_copy(
    kept_records: Sequence[RawFixture], stray_records: Sequence[RawFixture]
) -> int:
    """How many dropped records the calendar holds no copy of, which is what the drop loses.

    Most of what the filter drops repeats a match the calendar already lists, so dropping it
    costs nothing at all. What is left is the fixed template block every save carries, and on
    one save measured a few dozen unplayed matches dated before the calendar begins whose
    teams no club record covers. That remainder is small, but it is a real loss, so it is
    counted and reported rather than dropped in silence.
    """
    kept_keys = {_duplicate_key(raw_fixture) for raw_fixture in kept_records}
    return sum(1 for raw_fixture in stray_records if _duplicate_key(raw_fixture) not in kept_keys)


@dataclass(frozen=True, slots=True)
class _DecodedFixture:
    """One kept record with the values decoding and joining it produced."""

    raw: RawFixture
    date: datetime.date | None
    kick_off_time: datetime.time | None
    home_club: tuple[int, int] | None
    away_club: tuple[int, int] | None


def _sort_key(
    decoded: _DecodedFixture,
) -> tuple[datetime.date, datetime.time, int, int]:
    """A total order over the calendar: date, kick-off, then the two team ids.

    A record whose date does not decode sorts last, and one whose kick-off slot names no time
    sorts first within its day, so neither leaves the order resting on file position.
    """
    return (
        datetime.date.max if decoded.date is None else decoded.date,
        datetime.time.min if decoded.kick_off_time is None else decoded.kick_off_time,
        decoded.raw.home_team_id,
        decoded.raw.away_team_id,
    )


def _club_fields(
    club: tuple[int, int] | None, club_by_uid: Mapping[int, Club]
) -> tuple[int | None, str | None, str | None, int | None]:
    """(uid, name, short name, slot) of the club fielding a team, all None when it has none."""
    if club is None:
        return _NO_CLUB
    club_uid, team_slot = club
    club_record = club_by_uid.get(club_uid)
    if club_record is None:
        return club_uid, None, None, team_slot
    return club_uid, club_record.name, club_record.short_name, team_slot


def _modal_ordinals(
    ordinal_counts: Mapping[tuple[int, int | None], Mapping[int, int]], minimum_fixtures: int
) -> dict[tuple[int, int | None], int]:
    """The ground each club used most in each season, for the pairs that played enough at home.

    A pair with fewer than `minimum_fixtures` recorded grounds gets no entry, so no match of
    that pair is called neutral on the strength of one or two records. Two grounds used
    equally often leave the lower ordinal, so the answer never depends on record order.
    """
    return {
        vote_key: max(counts.items(), key=lambda entry: (entry[1], -entry[0]))[0]
        for vote_key, counts in ordinal_counts.items()
        if sum(counts.values()) >= minimum_fixtures
    }


def build_fixtures(
    span_records: SpanRecords,
    stage_index: StageIndex,
    competition_index: CompetitionIndex,
    club_index: ClubIndex,
    stadium_index: StadiumIndex,
    layout: FixtureCalendarLayout,
) -> tuple[tuple[Fixture, ...], FixtureStats]:
    """Decode the calendar, retaining the existing fixture-builder return shape."""
    fixtures, stats, _offsets = build_fixtures_with_offsets(
        span_records, stage_index, competition_index, club_index, stadium_index, layout
    )
    return fixtures, stats


def build_fixtures_with_offsets(
    span_records: SpanRecords,
    stage_index: StageIndex,
    competition_index: CompetitionIndex,
    club_index: ClubIndex,
    stadium_index: StadiumIndex,
    layout: FixtureCalendarLayout,
) -> tuple[tuple[Fixture, ...], FixtureStats, tuple[int, ...]]:
    """Decode, join and sort the calendar, and count what the fixture checks judge.

    The stadium each record stores is an ordinal into the stadium table, and the ordinal itself
    stays private: what a row carries is the uid that table gives it, which is the id the
    stadium table's own rows are keyed by. The same ordinal also decides `is_neutral_venue`,
    which compares grounds rather than naming one and so needs no uid at all.
    """
    # Proven counted cache children remain available in the raw span audit, but are
    # not calendar anchors. Exclude their votes inside the original physical runs.
    cache_offsets = frozenset(span_records.fixture_cache_offsets)
    raw_fixtures = tuple(
        record for record in span_records.fixtures if record.span_offset not in cache_offsets
    )
    cache_records_excluded = len(span_records.fixtures) - len(raw_fixtures)
    split_span = _split_span(span_records.fixtures, layout.cluster_gap_bytes, cache_offsets)
    kept_records = split_span.kept
    recovered: dict[int, RawFixture] = {}
    if kept_records:
        anchor_offsets = {record.span_offset for record in kept_records}
        for continuation in span_records.fixture_continuations:
            if (
                continuation.left_offset in anchor_offsets
                and continuation.right_offset in anchor_offsets
            ):
                for record in continuation.fixtures:
                    if (
                        continuation.left_offset < record.span_offset < continuation.right_offset
                        and record.span_offset not in cache_offsets
                    ):
                        recovered.setdefault(record.span_offset, record)
        # Original anchors always win a physical-position collision. Distinct positions,
        # including duplicate semantic fixture keys, remain distinct for result joins.
        for anchor in kept_records:
            recovered.pop(anchor.span_offset, None)
        if recovered:
            kept_records = tuple(
                sorted((*kept_records, *recovered.values()), key=lambda r: r.span_offset)
            )

    # Status belongs to the preceding optional-result prefix. Conflicting owned
    # contributions leave the original standalone admission as the fallback.
    played_by_offset: dict[int, bool | None] = {}
    for presence in span_records.fixture_presence:
        if (
            presence.span_offset in played_by_offset
            and played_by_offset[presence.span_offset] != presence.played
        ):
            played_by_offset[presence.span_offset] = None
        else:
            played_by_offset[presence.span_offset] = presence.played

    stage_by_id = stage_index.stage_by_id
    team_to_club = club_index.team_to_club
    club_by_uid = club_index.club_by_uid
    name_for = competition_index.name_for
    uid_by_ordinal = stadium_index.uid_by_ordinal
    # Only a couple of hundred grounds store a name, so this map is small and most
    # matches take no name from it.
    name_by_ordinal = {row.ordinal: row.name for row in stadium_index.rows if row.name is not None}
    round_index_none_value = layout.round_index_none_value

    decoded_records: list[_DecodedFixture] = []
    ordinal_counts: dict[tuple[int, int | None], dict[int, int]] = {}
    with_stage = 0
    stage_resolved = 0
    home_team_resolved = 0
    away_team_resolved = 0
    stub_team_references = 0
    undated = 0
    bad_kick_off_slots = 0
    with_stadium = 0
    stadium_resolved = 0

    for raw_fixture in kept_records:
        kick_off_date = decode_date(
            _DATE_WORDS.pack(raw_fixture.packed_kick_off, raw_fixture.kick_off_year), 0
        )
        if kick_off_date is None:
            undated += 1
        kick_off_time = kick_off_time_of(raw_fixture.packed_kick_off, layout)
        if kick_off_time is None:
            bad_kick_off_slots += 1
        stage_id = raw_fixture.stage_id
        if stage_id is not None:
            with_stage += 1
            if stage_id in stage_by_id:
                stage_resolved += 1
        home_club = team_to_club.get(raw_fixture.home_team_id)
        away_club = team_to_club.get(raw_fixture.away_team_id)
        if home_club is not None:
            home_team_resolved += 1
        elif raw_fixture.home_team_id in club_index.stub_team_ids:
            stub_team_references += 1
        if away_club is not None:
            away_team_resolved += 1
        elif raw_fixture.away_team_id in club_index.stub_team_ids:
            stub_team_references += 1
        stadium_ordinal = raw_fixture.stadium_ordinal
        if stadium_ordinal is not None:
            with_stadium += 1
            if stadium_ordinal in uid_by_ordinal:
                stadium_resolved += 1
        if home_club is not None and stadium_ordinal is not None:
            counts = ordinal_counts.setdefault((home_club[0], raw_fixture.season_start_year), {})
            counts[stadium_ordinal] = counts.get(stadium_ordinal, 0) + 1
        decoded_records.append(
            _DecodedFixture(raw_fixture, kick_off_date, kick_off_time, home_club, away_club)
        )

    modal_ordinals = _modal_ordinals(ordinal_counts, layout.neutral_venue_minimum_home_fixtures)
    decoded_records.sort(key=_sort_key)

    fixtures: list[Fixture] = []
    for decoded in decoded_records:
        raw_fixture = decoded.raw
        stage_id = raw_fixture.stage_id
        stage = None if stage_id is None else stage_by_id.get(stage_id)
        competition_id = None if stage is None else stage.competition_id
        home_uid, home_name, home_short_name, home_slot = _club_fields(
            decoded.home_club, club_by_uid
        )
        away_uid, away_name, away_short_name, away_slot = _club_fields(
            decoded.away_club, club_by_uid
        )
        stadium_ordinal = raw_fixture.stadium_ordinal
        is_neutral_venue: bool | None = None
        if decoded.home_club is not None and stadium_ordinal is not None:
            modal_ordinal = modal_ordinals.get(
                (decoded.home_club[0], raw_fixture.season_start_year)
            )
            if modal_ordinal is not None:
                is_neutral_venue = stadium_ordinal != modal_ordinal
        owned_played = played_by_offset.get(raw_fixture.span_offset)
        played = raw_fixture.played if owned_played is None else owned_played
        stored_round_index = raw_fixture.round_index
        fixtures.append(
            Fixture(
                stage_id=stage_id,
                competition_id=competition_id,
                competition_name=name_for(competition_id),
                round=None if stage is None else stage.round,
                round_index=(
                    None if stored_round_index == round_index_none_value else stored_round_index
                ),
                date=decoded.date,
                kick_off_time=decoded.kick_off_time,
                season_start_year=raw_fixture.season_start_year,
                home_team_id=raw_fixture.home_team_id,
                home_club_uid=home_uid,
                home_club_name=home_name,
                home_club_short_name=home_short_name,
                home_team_slot=home_slot,
                away_team_id=raw_fixture.away_team_id,
                away_club_uid=away_uid,
                away_club_name=away_name,
                away_club_short_name=away_short_name,
                away_team_slot=away_slot,
                home_goals=None,
                away_goals=None,
                played=played,
                is_neutral_venue=is_neutral_venue,
                stadium_uid=(
                    None if stadium_ordinal is None else uid_by_ordinal.get(stadium_ordinal)
                ),
                stadium_name=(
                    None if stadium_ordinal is None else name_by_ordinal.get(stadium_ordinal)
                ),
                match_record_id=raw_fixture.match_record_id if played else None,
                match_rules_template=raw_fixture.match_rules_template,
                unknown=FrozenMapping(
                    {
                        "date2": raw_fixture.date2,
                        "phase": raw_fixture.phase,
                        "leg": raw_fixture.leg,
                        "r39_42": raw_fixture.r39_42,
                        "r47_54": raw_fixture.r47_54,
                    }
                ),
            )
        )

    stats = FixtureStats(
        span_records=len(raw_fixtures) + len(recovered),
        cluster_records=len(kept_records),
        clusters=split_span.clusters,
        strays_without_a_copy=_strays_without_a_copy(kept_records, split_span.strays),
        with_stage=with_stage,
        stage_resolved=stage_resolved,
        home_team_resolved=home_team_resolved,
        away_team_resolved=away_team_resolved,
        undated=undated,
        bad_kick_off_slots=bad_kick_off_slots,
        neutral_venue_votes=len(modal_ordinals),
        with_stadium=with_stadium,
        stadium_resolved=stadium_resolved,
        stub_team_references=stub_team_references,
        cache_records_excluded=cache_records_excluded,
    )
    return tuple(fixtures), stats, tuple(decoded.raw.span_offset for decoded in decoded_records)
