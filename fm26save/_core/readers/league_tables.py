"""Live league tables, built from the blocks one span pass collected.

**The span holds each block several times over.** The copies agree in every field this reader
decodes -- the same team, the same five aggregates, the same match rows -- and differ only in
the 19 undecoded bytes stored in front of the block. About 45% of the blocks on every save
measured are such copies. Keeping them would put
one club in a table two, three or four times and invent standings no save holds, so they are
dropped on content before anything else happens, and how many were dropped is counted: a
reader that quietly stopped dropping them would pass every other check here.

**Each block stores its own place in its table**, in the first of those head bytes: the index
runs 0 to n-1 and starts again where the next table begins. That is the boundary between one
table and the next, and it is the save's own. The distance between blocks is not a boundary and
must not be used as one, because two adjacent tables sit as close together as the blocks inside
a single table: a 3,000-byte rule merged one group in six on the corpus, the managed club's own
20-club division among them, and numbered the joined rows 1 to 38 across the seam without any
check noticing.

Dropping the copies first is what keeps that index readable. A copy's stored index is not the
one the block it repeats carries, so a copy left inside a table breaks the run and splits the
table around it: on the corpus the kept blocks give hundreds to about a thousand tables, the
largest holding 36, while the same blocks undeduplicated shatter into several thousand. The
tables that survive are the right shape -- dozens of them are divisions whose clubs all play
each other twice -- and at most 0.3% still hold one club twice, where two adjacent tables
happen to chain their indexes.

Nothing in a table names its competition. It is voted for from the fixture calendar: the
competitions each member club plays in are tallied over the table, and the most covered one
names it if it covers at least half the members, so a competition one member of twelve plays in
never names the table. Several tables may name one competition, because a cup's group stage is
one competition with a table per group; the corpus holds about 800 tables against about 520
competitions, so reserving a competition for a single table would leave most tables unnamed. A
table the vote cannot settle keeps `competition_id` None and is still returned, which on the
corpus is about one table in a thousand.

**That headline overshoots the 85% the spec expects, and it must be read beside the shape of
the tables.** The vote settles almost every table on the saves measured, but a third to nearly
a half of tables hold a single block, and a one-block table meets the
half-the-members rule on a majority of one, so it resolves whatever the calendar says. Over the
tables of two blocks or more the share is 0.998 or better. That is the figure that
shows the vote is sound rather than merely permissive, and a minimum size for the vote is worth
weighing against it.

**Each match slot says which ground it was played at**, from the parity the save alternates
venue by: the even slots are the home ones. The calendar is what says so, and it says it again
on every save read. For each table whose every row's played count equals that club's played
calendar fixtures in the table's competition in exactly one season, each played slot is matched
to the meetings the calendar holds between those two clubs in that season; where one of them
has been played, or where the scores name one of them and only one, the calendar's own stored
home team gives the venue. Those slots are then compared with the parity's: all but about a
fifth of a percent agree on every save measured, against that same fifth of a percent had
the parity been the other way round. Out-of-step tables are left out, because a table that does
not account for a season is compared against the wrong meetings; over every table the agreement
falls to about 0.91.

Every join goes through an index another reader already built, and an id that does not resolve
leaves its fields empty and is counted rather than guessed.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import LeagueTableLayout
from fm26save._core._reader_stats import LeagueTableStats
from fm26save._core.models.clubs import Club
from fm26save._core.models.fixtures import Fixture
from fm26save._core.models.league_tables import (
    LeagueTable,
    LeagueTableMatch,
    LeagueTableRow,
    LeagueTableSplit,
    MatchOutcome,
    MatchSide,
)
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.competitions import CompetitionIndex
from fm26save._core.readers.span import RawTableBlock, RawTableRow, SpanRecords

# The five aggregate rows, in the order the save stores them.
_TOTAL, _HOME, _AWAY, _FIRST_HALF, _SECOND_HALF = range(5)
_NO_CLUB: tuple[int | None, str | None, str | None, int | None] = (None, None, None, None)


def _content_key(block: RawTableBlock) -> tuple[object, ...]:
    """Everything the block stores except the 19 undecoded head bytes and where it sits.

    The head bytes are left out on purpose: they are the only field in which the save's copies
    of one block differ, so a key that included them would call every copy distinct and drop
    almost nothing (about 1% on the saves measured, against 45% here).
    """
    return (block.team_id, block.rounds_per_venue, block.aggregates, block.matches)


def distinct_blocks(
    blocks: Sequence[RawTableBlock],
) -> tuple[tuple[RawTableBlock, ...], int]:
    """The blocks with repeated content removed, and how many were removed.

    The first copy in span order is the one kept, so the result never depends on anything but
    the order the span holds. The kept copy's head bytes are the ones reported, and the others
    are lost; nothing distinguishes them, so there is no better copy to prefer.
    """
    kept: list[RawTableBlock] = []
    seen: set[tuple[object, ...]] = set()
    for block in blocks:
        key = _content_key(block)
        if key in seen:
            continue
        seen.add(key)
        kept.append(block)
    return tuple(kept), len(blocks) - len(kept)


def group_blocks(
    blocks: Sequence[RawTableBlock], layout: LeagueTableLayout
) -> tuple[tuple[RawTableBlock, ...], ...]:
    """Split blocks into tables on the index each block stores of its own place in one.

    The head byte at `stored_index_head_byte` counts the block's place in its table, 0 to
    n-1, and starts again at 0 when the next table begins, so a block whose index does not
    carry on from the block before it begins a new table. This is the save's own boundary: it
    needs no distance constant, no competition name and no knowledge of any country's leagues.

    The distance between blocks is not used, and must not be: the blocks of two adjacent
    tables are stored as close together as the blocks inside one, so a distance rule runs
    tables together. On the corpus it merged one group in six, the managed club's own division
    among them.

    Pass the blocks through `distinct_blocks` first. The save writes each table twice and the
    second copy's indexes are a permutation rather than a run, so a copy left in the middle of
    a table breaks the run and splits the table around it.
    """
    if not blocks:
        return ()
    index_byte = layout.stored_index_head_byte
    groups: list[tuple[RawTableBlock, ...]] = []
    current: list[RawTableBlock] = []
    previous_index: int | None = None
    for block in blocks:
        stored_index = block.head_bytes[index_byte]
        if previous_index is not None and stored_index != previous_index + 1:
            groups.append(tuple(current))
            current = []
        current.append(block)
        previous_index = stored_index
    groups.append(tuple(current))
    return tuple(groups)


def competition_counts_by_team(fixtures: Sequence[Fixture]) -> dict[int, Counter[int]]:
    """How often each team id appears in each competition, from the fixture calendar.

    Both sides of a fixture count, since a match places both clubs in the competition. A
    fixture whose stage names no competition is skipped rather than counted under a placeholder.
    """
    counts_by_team: dict[int, Counter[int]] = {}
    for fixture in fixtures:
        competition_id = fixture.competition_id
        if competition_id is None:
            continue
        for team_id in (fixture.home_team_id, fixture.away_team_id):
            team_counts = counts_by_team.get(team_id)
            if team_counts is None:
                team_counts = Counter[int]()
                counts_by_team[team_id] = team_counts
            team_counts[competition_id] += 1
    return counts_by_team


def resolve_group_competitions(
    groups: Sequence[Sequence[RawTableBlock]], counts_by_team: Mapping[int, Counter[int]]
) -> tuple[int | None, ...]:
    """Vote each table's competition from the calendar; one entry per table, in table order.

    The competitions each member club plays in are tallied over the table, and the most
    covered one names it provided it covers at least half the members, so a competition one
    member of twelve plays in never names the table. Ties are settled on the lower id, so the
    result never depends on the order a dictionary happened to hold two competitions in.

    Two tables may name the same competition, and most competitions name several: a cup's
    group stage is one competition holding a table per group, and the corpus holds about 800
    tables against about 520 competitions. An earlier rule reserved each competition for one
    table; under the stored-index boundary that starves the rest, and resolution falls from
    almost every table to two in five.
    """
    resolved: list[int | None] = []
    for members in groups:
        tally: Counter[int] = Counter()
        for block in members:
            # One vote per member per competition, so a club with forty league fixtures does
            # not outvote the rest of its own table.
            for competition_id in counts_by_team.get(block.team_id, ()):
                tally[competition_id] += 1
        if not tally:
            resolved.append(None)
            continue
        competition_id, members_covered = min(
            tally.items(), key=lambda entry: (-entry[1], entry[0])
        )
        needed = math.ceil(len(members) / 2)
        resolved.append(competition_id if members_covered >= needed else None)
    return tuple(resolved)


def _club_fields(
    team_id: int, club_index: ClubIndex, layout: LeagueTableLayout
) -> tuple[int | None, str | None, str | None, int | None]:
    """(uid, name, short name, slot) of the club fielding a team, all None when it has none."""
    lowest_team_id, highest_team_id = layout.team_id_range
    if not lowest_team_id <= team_id <= highest_team_id:
        return _NO_CLUB
    club = club_index.team_to_club.get(team_id)
    if club is None:
        return _NO_CLUB
    club_uid, team_slot = club
    club_record: Club | None = club_index.club_by_uid.get(club_uid)
    if club_record is None:
        return club_uid, None, None, team_slot
    return club_uid, club_record.name, club_record.short_name, team_slot


def _split(row: RawTableRow) -> LeagueTableSplit:
    return LeagueTableSplit(
        played=row.played,
        won=row.won,
        drawn=row.drawn,
        lost=row.lost,
        goals_for=row.goals_for,
        goals_against=row.goals_against,
        points=row.points,
    )


def _outcome(row: RawTableRow) -> MatchOutcome | None:
    """WIN, DRAW or LOSS from the row's own counters, or None when they name no single result."""
    if row.won == 1:
        return MatchOutcome.WIN
    if row.drawn == 1:
        return MatchOutcome.DRAW
    if row.lost == 1:
        return MatchOutcome.LOSS
    return None


def _venue(slot: int, layout: LeagueTableLayout) -> MatchSide | None:
    """Which side of the match the row's club was, or None when a layout leaves the parity unset.

    The save alternates the side with the slot's parity and never says which parity is home. The
    fixture calendar says it, because a calendar record stores its home team outright: on the
    tables whose rows account for exactly one season of that calendar, the slots the calendar
    can settle by itself are home where the even slot is home on at least 99.76% of them on
    every save measured, and where the odd slot is home on a fifth of a percent.
    `_venue_agreement` re-runs that comparison on every save read, so the parity this returns
    is checked rather than assumed.

    A slot never played gets a side too: the parity belongs to the slot, not to what happened
    in it, so the shape of a season stays readable where the season is unplayed.
    """
    home_slot_parity = layout.home_slot_parity
    if home_slot_parity is None:
        return None
    return MatchSide.HOME if slot % 2 == home_slot_parity else MatchSide.AWAY


def _match_rows(
    block: RawTableBlock, club_index: ClubIndex, layout: LeagueTableLayout
) -> tuple[LeagueTableMatch, ...]:
    """One entry per match slot, keeping the slots the club never played."""
    matches: list[LeagueTableMatch] = []
    for slot, row in enumerate(block.matches):
        venue = _venue(slot, layout)
        if row.key == layout.unplayed_key:
            matches.append(
                LeagueTableMatch(
                    slot=slot,
                    home_or_away=venue,
                    opponent_team_id=None,
                    opponent_club_uid=None,
                    opponent_club_name=None,
                    opponent_club_short_name=None,
                    goals_for=None,
                    goals_against=None,
                    outcome=None,
                    points=None,
                )
            )
            continue
        club_uid, club_name, club_short_name, _team_slot = _club_fields(row.key, club_index, layout)
        matches.append(
            LeagueTableMatch(
                slot=slot,
                home_or_away=venue,
                opponent_team_id=row.key,
                opponent_club_uid=club_uid,
                opponent_club_name=club_name,
                opponent_club_short_name=club_short_name,
                goals_for=row.goals_for,
                goals_against=row.goals_against,
                outcome=_outcome(row),
                points=row.points,
            )
        )
    return tuple(matches)


def _club_pair(one_team_id: int, other_team_id: int) -> tuple[int, int]:
    """The two team ids in a fixed order, so one meeting has one key whichever side asks."""
    if one_team_id <= other_team_id:
        return one_team_id, other_team_id
    return other_team_id, one_team_id


@dataclass(frozen=True, slots=True)
class _CalendarMeetings:
    """The fixture calendar indexed the two ways the venue check reads it.

    `played_per_team` counts each club's played fixtures per competition and season, which is
    what says whether a table's rows account for a season. `meetings` holds the fixtures
    between one pair of clubs in one competition and season, at either ground, which is what a
    slot is compared against. `seasons` lists the seasons each competition has fixtures in.

    A fixture whose season did not decode is left out of all three: it cannot place a match in
    a season, so it has no business in a check about which season a table describes.
    """

    played_per_team: dict[tuple[int, int, int], int]
    meetings: dict[tuple[int, int, tuple[int, int]], list[Fixture]]
    seasons: dict[int, set[int]]


def _index_calendar(fixtures: Sequence[Fixture]) -> _CalendarMeetings:
    played_per_team: dict[tuple[int, int, int], int] = {}
    meetings: dict[tuple[int, int, tuple[int, int]], list[Fixture]] = {}
    seasons: dict[int, set[int]] = {}
    for fixture in fixtures:
        competition_id = fixture.competition_id
        season = fixture.season_start_year
        if competition_id is None or season is None:
            continue
        seasons.setdefault(competition_id, set()).add(season)
        home_team_id = fixture.home_team_id
        away_team_id = fixture.away_team_id
        meetings.setdefault(
            (competition_id, season, _club_pair(home_team_id, away_team_id)), []
        ).append(fixture)
        if fixture.played:
            for team_id in (home_team_id, away_team_id):
                played_key = (competition_id, season, team_id)
                played_per_team[played_key] = played_per_team.get(played_key, 0) + 1
    return _CalendarMeetings(played_per_team, meetings, seasons)


def _season_in_step(
    competition_id: int, rows: Sequence[LeagueTableRow], calendar: _CalendarMeetings
) -> int | None:
    """The one season whose played counts match every row of a table, or None.

    A table matching two seasons is turned away as firmly as one matching none: the population
    is worth having only where there is no doubt which season the row counts describe. On the
    corpus a handful of tables per save match two.
    """
    in_step: int | None = None
    seasons_matched = 0
    for season in calendar.seasons.get(competition_id, ()):
        if all(
            row.played == calendar.played_per_team.get((competition_id, season, row.team_id), 0)
            for row in rows
        ):
            in_step = season
            seasons_matched += 1
    return in_step if seasons_matched == 1 else None


def _decided_venue(
    row_team_id: int, slot: LeagueTableMatch, meetings: Sequence[Fixture]
) -> MatchSide | None:
    """The side the calendar itself gives a played slot, or None where it cannot say.

    One played meeting between the two clubs settles it outright, from that record's own
    stored home team. Where both meetings have been played the scores decide, and only when
    every played meeting carries one and exactly one of them is the slot's own score read from
    the row club's side: two meetings that ended alike say nothing and are left undecided. On
    the corpus the first rule decides thousands of slots and the second several hundred to a
    couple of thousand, with most slots left undecided.
    """
    played = [fixture for fixture in meetings if fixture.played]
    if len(played) == 1:
        return MatchSide.HOME if played[0].home_team_id == row_team_id else MatchSide.AWAY
    if not played:
        return None
    row_club_at_home: list[bool] = []
    for fixture in played:
        home_goals = fixture.home_goals
        away_goals = fixture.away_goals
        if home_goals is None or away_goals is None:
            return None
        at_home = fixture.home_team_id == row_team_id
        scored = home_goals if at_home else away_goals
        conceded = away_goals if at_home else home_goals
        if scored == slot.goals_for and conceded == slot.goals_against:
            row_club_at_home.append(at_home)
    if len(row_club_at_home) != 1:
        return None
    return MatchSide.HOME if row_club_at_home[0] else MatchSide.AWAY


@dataclass(frozen=True, slots=True)
class _VenueAgreement:
    """How far the slot parity's venues agree with the fixture calendar's own home teams."""

    in_sync_tables: int
    slots_decided: int
    slots_agreeing: int


def _venue_agreement(
    tables: Sequence[LeagueTable], fixtures: Sequence[Fixture], layout: LeagueTableLayout
) -> _VenueAgreement:
    """Check the slot parity against the calendar, on the tables entitled to judge it.

    A table is entitled when it has a competition and its every row's played count equals that
    club's played calendar fixtures in the competition in exactly one season: the row counts
    then describe that season and no other, so a slot can be matched to the meeting it records.
    Out-of-step tables are compared against the wrong meetings, and over every table instead of
    these the agreement falls from 0.998 to 0.91 on the corpus, so the population is the check.

    Nothing is read here that the two readers have not already returned, and no second pass
    over the span happens: the tables are the ones just built and the fixtures the calendar
    the caller passed in. A layout that settles no parity checks nothing at all, since there
    is then no venue to compare.
    """
    if layout.home_slot_parity is None:
        return _VenueAgreement(0, 0, 0)
    calendar = _index_calendar(fixtures)
    in_sync_tables = 0
    slots_decided = 0
    slots_agreeing = 0
    for table in tables:
        competition_id = table.competition_id
        if competition_id is None:
            continue
        season = _season_in_step(competition_id, table.rows, calendar)
        if season is None:
            continue
        in_sync_tables += 1
        for row in table.rows:
            row_team_id = row.team_id
            for slot in row.matches:
                opponent_team_id = slot.opponent_team_id
                if opponent_team_id is None:
                    continue
                meeting_key = (
                    competition_id,
                    season,
                    _club_pair(row_team_id, opponent_team_id),
                )
                decided = _decided_venue(row_team_id, slot, calendar.meetings.get(meeting_key, ()))
                if decided is None:
                    continue
                slots_decided += 1
                if decided is slot.home_or_away:
                    slots_agreeing += 1
    return _VenueAgreement(in_sync_tables, slots_decided, slots_agreeing)


@dataclass(frozen=True, slots=True)
class _GroupCounts:
    """What building one group's rows counted, for the league-table checks."""

    team_id_in_range: int
    team_resolved: int


def _rows_for(
    group: Sequence[RawTableBlock], club_index: ClubIndex, layout: LeagueTableLayout
) -> tuple[tuple[LeagueTableRow, ...], _GroupCounts]:
    lowest_team_id, highest_team_id = layout.team_id_range
    rows: list[LeagueTableRow] = []
    team_id_in_range = 0
    team_resolved = 0
    for position, block in enumerate(group, start=1):
        team_id = block.team_id
        if lowest_team_id <= team_id <= highest_team_id:
            team_id_in_range += 1
        club_uid, club_name, club_short_name, team_slot = _club_fields(team_id, club_index, layout)
        if club_uid is not None:
            team_resolved += 1
        total = block.aggregates[_TOTAL]
        rows.append(
            LeagueTableRow(
                position=position,
                team_id=team_id,
                club_uid=club_uid,
                club_name=club_name,
                club_short_name=club_short_name,
                team_slot=team_slot,
                played=total.played,
                won=total.won,
                drawn=total.drawn,
                lost=total.lost,
                goals_for=total.goals_for,
                goals_against=total.goals_against,
                points=total.points,
                home=_split(block.aggregates[_HOME]),
                away=_split(block.aggregates[_AWAY]),
                first_half=_split(block.aggregates[_FIRST_HALF]),
                second_half=_split(block.aggregates[_SECOND_HALF]),
                rounds_per_venue=block.rounds_per_venue,
                matches=_match_rows(block, club_index, layout),
                unknown=FrozenMapping(
                    dict(zip(LeagueTableRow.UNKNOWN_KEYS, block.head_bytes, strict=True))
                ),
            )
        )
    return tuple(rows), _GroupCounts(team_id_in_range, team_resolved)


def _is_double_round_robin_division(
    rows: Sequence[LeagueTableRow], layout: LeagueTableLayout
) -> bool:
    """Whether the group has the shape of a division whose clubs all play each other twice.

    A shape rule, not a name: it holds in any country and needs no competition name, which is
    what keeps it inside the rule that a meaning is named only where a displayed label pins it.
    """
    fewest_clubs, most_clubs = layout.division_club_range
    return fewest_clubs <= len(rows) <= most_clubs and rows[0].rounds_per_venue == len(rows) - 1


def started_calendar_divisions(fixtures: Sequence[Fixture], layout: LeagueTableLayout) -> int:
    """How many divisions the calendar shows under way, each of which should hold a table.

    A division here is a stage's latest season whose fixtures pair every two member teams
    exactly once each way, with a club count inside the layout's division range: the
    calendar's own form of the table shape `_is_double_round_robin_division` counts. It is
    under way once every member team has played in it. The reader keeps only blocks with a
    played match, so a division where a member has yet to play cannot keep its table's shape,
    and before the season starts it has no table at all. Only a stage's latest season counts,
    so a finished season does not stand in for one not yet begun.
    """
    fewest_clubs, most_clubs = layout.division_club_range
    by_stage_season: dict[tuple[int, int], list[Fixture]] = {}
    latest_season: dict[int, int] = {}
    for fixture in fixtures:
        stage_id = fixture.stage_id
        season = fixture.season_start_year
        if stage_id is None or season is None:
            continue
        by_stage_season.setdefault((stage_id, season), []).append(fixture)
        latest_season[stage_id] = max(season, latest_season.get(stage_id, season))
    started = 0
    for (stage_id, season), stage_fixtures in by_stage_season.items():
        if season != latest_season[stage_id]:
            continue
        pairs = {(fixture.home_team_id, fixture.away_team_id) for fixture in stage_fixtures}
        teams = {team_id for pair in pairs for team_id in pair}
        club_count = len(teams)
        if (
            not fewest_clubs <= club_count <= most_clubs
            or len(stage_fixtures) != club_count * (club_count - 1)
            or len(pairs) != len(stage_fixtures)
        ):
            continue
        teams_played = {
            team_id
            for fixture in stage_fixtures
            if fixture.played
            for team_id in (fixture.home_team_id, fixture.away_team_id)
        }
        if len(teams_played) == club_count:
            started += 1
    return started


def build_league_tables(
    span_records: SpanRecords,
    fixtures: Sequence[Fixture],
    competition_index: CompetitionIndex,
    club_index: ClubIndex,
    layout: LeagueTableLayout,
) -> tuple[tuple[LeagueTable, ...], LeagueTableStats]:
    """Deduplicate, group, vote and join the span's table blocks into live tables.

    `fixtures` is the calendar the fixtures reader returned, so the vote runs on rows whose own
    checks have already passed rather than on the raw span records. The same calendar then
    checks the slot parity every match row's venue comes from, on the tables whose rows account
    for exactly one season of it; that costs one more read of the rows already built and no
    further pass over the span.
    """
    kept_blocks, duplicate_blocks = distinct_blocks(span_records.table_blocks)
    groups = group_blocks(kept_blocks, layout)
    resolved = resolve_group_competitions(groups, competition_counts_by_team(fixtures))
    name_for = competition_index.name_for

    tables: list[LeagueTable] = []
    groups_resolved = 0
    blocks_in_resolved_groups = 0
    team_id_in_range = 0
    team_resolved = 0
    double_round_robin_divisions = 0
    for position, group in enumerate(groups):
        rows, counts = _rows_for(group, club_index, layout)
        team_id_in_range += counts.team_id_in_range
        team_resolved += counts.team_resolved
        competition_id = resolved[position]
        if competition_id is not None:
            groups_resolved += 1
            blocks_in_resolved_groups += len(rows)
        if _is_double_round_robin_division(rows, layout):
            double_round_robin_divisions += 1
        tables.append(
            LeagueTable(
                competition_id=competition_id,
                competition_name=name_for(competition_id),
                club_count=len(rows),
                rows=rows,
            )
        )

    venue_agreement = _venue_agreement(tables, fixtures, layout)
    stats = LeagueTableStats(
        blocks=len(kept_blocks),
        duplicate_blocks=duplicate_blocks,
        block_candidates=span_records.table_block_candidates,
        groups=len(groups),
        groups_resolved=groups_resolved,
        blocks_in_resolved_groups=blocks_in_resolved_groups,
        team_id_in_range=team_id_in_range,
        team_resolved=team_resolved,
        double_round_robin_divisions=double_round_robin_divisions,
        started_calendar_divisions=started_calendar_divisions(fixtures, layout),
        in_sync_tables=venue_agreement.in_sync_tables,
        venue_slots_decided=venue_agreement.slots_decided,
        venue_slots_agreeing=venue_agreement.slots_agreeing,
    )
    return tuple(tables), stats
