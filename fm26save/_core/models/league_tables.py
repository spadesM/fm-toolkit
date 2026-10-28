"""Live league tables: one table per group of blocks, one row per club in it.

A table is a group of blocks the save stores together, not a record with a header: nothing in
the group names its competition, so the competition is voted for from the fixture calendar and
is None on the groups the vote cannot settle. Those groups are still returned.

`LeagueTableRow.position` is the club's place in the table, counting from one. The save stores
each table already in standings order, so this is the league position and the rows need no
sorting. Do not re-sort them: the game separates clubs level on points by their results against
each other first, and no field here carries that, so a sort by points and goal difference moves
clubs the save had in the right order. That sort reproduces the stored order on about 9 tables
in 10 across the saves measured, and on about 7 in 10 of the division-shaped ones; the
disagreements are where the head-to-head rule decides.

Derived views these records carry no field for:

- goal difference is `goals_for - goals_against`;
- a division is `18 <= club_count <= 26 and rows[0].rounds_per_venue == club_count - 1`, a shape
  rule that holds in any country and needs no competition name;
- a club's remaining fixtures are the set difference between the group's member teams and the
  opponents already in `matches`, per venue; the save stores no remaining-fixture list;
- resolved groups only is `.filter(lambda table: table.competition_id is not None)`;
- a club's row in a competition is `.where(competition_id=...)` and then the row whose
  `club_uid` matches. fmsave never picks the group for the caller, because a club is in several
  groups at once.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses


class MatchSide(StrEnum):
    """Which side of a match a club was, the home one or the away one.

    This is the club's side, not the ground the match was played at: a match at a neutral
    ground still has a home club and an away club, and this says which of the two the row's
    club was. `Fixture.is_neutral_venue` is the field about the ground.

    Derived by fmsave, never read as a code.
    """

    HOME = "home"
    AWAY = "away"


class MatchOutcome(StrEnum):
    """How a match row ended. Derived by fmsave from the row's counters, never read as a code."""

    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"


@dataclass(frozen=True, slots=True)
class LeagueTableSplit:
    """One of a row's four partial records: home, away, first half or second half.

    Every field is unconfirmed. The save's own arithmetic holds on all four (played equals won
    plus drawn plus lost, and home and away add up to the total, as do the two halves), which
    is what the block acceptance checks require, but no in-game screen has yet been read back
    against them, so none of the seven is verified.

    Attributes:
        played: Matches played in this split (unconfirmed).
        won: Matches won (unconfirmed).
        drawn: Matches drawn (unconfirmed).
        lost: Matches lost (unconfirmed).
        goals_for: Goals scored (unconfirmed).
        goals_against: Goals conceded (unconfirmed).
        points: Points taken (unconfirmed).
    """

    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    points: int


@dataclass(frozen=True, slots=True)
class LeagueTableMatch:
    """One match slot of one club's row: a played match, or a slot never played.

    A slot the club has not played keeps its place in the list so the shape of the season is
    never lost: its opponent fields, goals, outcome and points are all None.

    Attributes:
        slot: The slot's index in the row, counting from zero.
        home_or_away: Which side of the match the row's club was, the home one or the away
            one, which the save stores as the slot's parity: the even slots are the home ones.
            That is checked against the fixture calendar's own stored home team on every table
            whose rows account for exactly one season of it, and it holds on 99.76% to 99.87%
            of the slots the calendar can settle by itself, against a fifth of a percent were
            the parity the other way round; the handful that disagree are consistent with
            rescheduled or neutral-ground meetings. A slot never played carries a side too,
            since the parity belongs to the slot rather than to what happened in it. It is None
            only where the build fmsave read the save with has not settled the parity. This is
            the club's side and not the ground: `Fixture.is_neutral_venue` is the field that
            says whether a match was played away from the home club's usual ground, and a
            match at a neutral ground still has a home club and an away club.
        opponent_team_id: The opponent's team id exactly as stored, or None for an unplayed
            slot.
        opponent_club_uid: Uid of the club fielding the opponent, or None when the slot is
            unplayed or no club lists that team.
        opponent_club_name: Denormalised name of opponent_club_uid, or None when it does not
            resolve.
        opponent_club_short_name: Denormalised short name of opponent_club_uid, or None when it
            does not resolve.
        goals_for: Goals the club scored, or None for an unplayed slot.
        goals_against: Goals the club conceded, or None for an unplayed slot.
        outcome: Whether the club won, drew or lost, or None for an unplayed slot and for a row
            whose counters name no single result.
        points: Points the club took from the match, or None for an unplayed slot.
    """

    slot: int
    home_or_away: MatchSide | None
    opponent_team_id: int | None
    opponent_club_uid: int | None
    opponent_club_name: str | None
    opponent_club_short_name: str | None
    goals_for: int | None
    goals_against: int | None
    outcome: MatchOutcome | None
    points: int | None


@dataclass(frozen=True, slots=True)
class LeagueTableRow:
    """One club's row in one live table, with its splits and its match slots.

    The seven top-level counters are the block's TOTAL aggregate; `home`, `away`, `first_half`
    and `second_half` are the other four, in the order the save stores them.

    Attributes:
        position: The club's place in the table, counting from one, which is the order the
            save stores. Read it as the league position and leave the rows alone: a sort by
            points and goal difference reproduces it on about 92% of tables and disagrees only
            where the game's own first tie-break, the results between the clubs level on
            points, decides an order these fields cannot reconstruct.
        team_id: The club's first-team id exactly as stored.
        club_uid: Uid of the club fielding that team, or None when no club lists it.
        club_name: Denormalised name of club_uid, or None when the team does not resolve.
        club_short_name: Denormalised short name of club_uid, or None when the team does not
            resolve.
        team_slot: The team's slot in its club's team list, 0 for the first entry, or None when
            the team does not resolve (unconfirmed).
        played: Matches played in total.
        won: Matches won in total.
        drawn: Matches drawn in total.
        lost: Matches lost in total.
        goals_for: Goals scored in total.
        goals_against: Goals conceded in total.
        points: Points taken in total.
        home: The club's home record (every field unconfirmed).
        away: The club's away record (every field unconfirmed).
        first_half: The club's record in the first half of the season (every field
            unconfirmed).
        second_half: The club's record in the second half of the season (every field
            unconfirmed).
        rounds_per_venue: How many rounds the group plays at each venue, so the row holds twice
            this many match slots (unconfirmed).
        matches: One entry per match slot, in stored order, including slots never played.
        unknown: The 19 bytes stored in front of the block, one int per byte. The first of
            them is the row's own place in its table, which is what tells one table from the
            next and is already reported as `position`; it is kept here so the blob ships
            whole. The other 18 are undecoded, and they are the only fields in which the
            save's several copies of a block differ (unconfirmed).
    """

    position: int
    team_id: int
    club_uid: int | None
    club_name: str | None
    club_short_name: str | None
    team_slot: int | None
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    points: int
    home: LeagueTableSplit
    away: LeagueTableSplit
    first_half: LeagueTableSplit
    second_half: LeagueTableSplit
    rounds_per_venue: int
    matches: tuple[LeagueTableMatch, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = tuple(
        f"head_minus_19_{index:02d}" for index in range(19)
    )


@dataclass(frozen=True, slots=True)
class LeagueTable:
    """One live table: every club the save groups together, with its rows.

    The rows nest, so a CSV export puts the whole list in one JSON cell. `to_dicts()` and the
    JSON writers are the useful exports for tables.

    Attributes:
        competition_id: The competition the table was voted to belong to, in the stage id
            space (not the id space a suspension's competition id belongs to); None when the
            vote could not settle it, which on the corpus is one table in a thousand. Read that
            beside the shape of the tables: 30% to 43% of them hold one block, and a one-block
            table meets the vote's half-the-members rule on a majority of one, so it resolves
            trivially; over the tables of two blocks or more resolution is 0.998 to 1.000. One
            competition names several tables, because a cup's group stage is one competition
            holding a table per group. The save stores no link from a table to its
            competition, so this is a vote on the fixture calendar rather than a stored value
            (unconfirmed).
        competition_name: Denormalised name of competition_id, which is None unless a name map
            is supplied, because the save stores no competition names (unconfirmed).
        club_count: How many rows the table holds (unconfirmed).
        rows: One row per club, in the order the save stores the group.
    """

    competition_id: int | None
    competition_name: str | None
    club_count: int
    rows: tuple[LeagueTableRow, ...]


register_field_statuses(
    LeagueTableSplit,
    unconfirmed=("played", "won", "drawn", "lost", "goals_for", "goals_against", "points"),
)
register_field_statuses(
    LeagueTableMatch,
    verified=(
        "slot",
        "home_or_away",
        "opponent_team_id",
        "opponent_club_uid",
        "opponent_club_name",
        "opponent_club_short_name",
        "goals_for",
        "goals_against",
        "outcome",
        "points",
    ),
)
register_field_statuses(
    LeagueTableRow,
    verified=(
        "position",
        "team_id",
        "club_uid",
        "club_name",
        "club_short_name",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "points",
        "matches",
    ),
    unconfirmed=("team_slot", "rounds_per_venue", "unknown"),
)
register_field_statuses(
    LeagueTable,
    verified=("rows",),
    unconfirmed=("competition_id", "competition_name", "club_count"),
)
