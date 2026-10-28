"""Per-match player records: what one player did in one match the save still holds.

Stored match histories may omit older matches and are not guaranteed season or career totals.
Rows do not mark their histories as truncated, so summing them can undercount a player's season.
Use `player_season_stats()` for the stored current-season totals. Friendlies, internationals and
youth matches are outside this reader's coverage.

A record's `competition_id` belongs to the **stage** id space, the same space `stages()`,
`fixtures()`, the league tables and `Suspension.competition_id` use, so all of them join.

The position a record stores is a bit mask of this structure's own, and a bit of it means
nothing anywhere else in the save.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


class MatchPosition(IntEnum):
    """The position a player filled in one match, for the mask bits whose meaning is confirmed.

    The save stores the position as a 16-bit mask carrying exactly one bit, and a member's
    value here is that bit's index, not the mask. Fourteen of the sixteen bits carry records on
    every save measured, so the mask covers a full set of positions; only one of them is named.

    A bit earns a name only where a position label the game itself displayed was matched to that
    exact bit, and only the goalkeeper bit is. Every record of a player the game labels "GK"
    carries this bit, and all but one of the records carrying it, over every save measured,
    belongs to a player the save rates a goalkeeper. No other bit has such a label: the players
    whose displayed label would separate one bit from its neighbours play several positions, so
    their label fits more than one bit, and a bit named from a neighbouring bit's meaning would
    be silently wrong where a raw mask is plainly incomplete.

    What the other bits are is therefore left open, and the raw mask is kept on every record so
    a caller can group by it. Grouping by the raw mask is sound whatever the bits mean; reading
    a position into one is not.

    A mask that is zero, carries a bit no label names, or carries more than one bit reads as
    UNKNOWN with its raw value kept. Fewer than five records per save carry a zero mask and none
    at all carries two bits.
    """

    UNKNOWN = -1
    GOALKEEPER = 0


@dataclass(frozen=True, slots=True)
class PlayerMatchStats:
    """One player's record of one match the save still holds.

    These rows are retained match histories, not guaranteed season or career totals. Older
    matches can be missing, and a row does not mark its history as truncated. Friendlies,
    internationals and youth matches are kept apart from these records and are not here at all.

    `competition_id` belongs to the **stage** id space, the same space `stages()`, `fixtures()`,
    the league tables and `Suspension.competition_id` use, so all of them join.

    Attributes:
        player_uid: Uid of the player the record belongs to, which is the player whose object
            holds it (unconfirmed).
        player_name: Denormalised name of player_uid (unconfirmed).
        date: The date the match was played.
        competition_id: Id of the competition, in the **stage** id space. It is stored on the
            record itself rather than reached through a stage.
        opponent_team_id: The opposing side's first-team id, exactly as stored. It is a team
            id and never a club index.
        opponent_club_uid: Uid of the club fielding the opposing team, or None when no club
            lists that team.
        opponent_club_name: Denormalised name of opponent_club_uid, or None when the team does
            not resolve.
        opponent_club_short_name: Denormalised short name of opponent_club_uid, or None when
            the team does not resolve.
        opponent_team_slot: The opposing team's slot in its club's team list, 0 for the first
            entry, or None when the team does not resolve (unconfirmed).
        has_stats: Whether the save still holds this match's statistics. A save that has
            dropped them keeps the date, the competition and the opponent and nothing else, so
            every field below that can be None is None when this is false (unconfirmed).
        position: The position played, as a coded value over the mask the record stores. Only
            the goalkeeper bit is named; every other mask keeps its raw value and reads as
            UNKNOWN. None when the save holds no statistics for the match.
        minutes: Minutes played, or None when the save holds no statistics for the match. No
            value the game displays has been matched to this number; what says it is minutes
            played is its shape. On the saves measured about half the matches with statistics
            hold exactly 90, over 0.993 hold 90 or less, none holds more than 130, and the rest
            are spread over the values below 90 rather than clustered (unconfirmed).
        left_at_minute: The minute the player left the pitch, whether he was substituted or
            sent off. None when he was on it at the final whistle, which the save stores as a
            zero, and None as well when the save holds no statistics for the match; `has_stats`
            tells those two apart. It is never 0, so a filter such as `left_at_minute < 10`
            selects the early departures and nobody else (unconfirmed).
        goals: Goals scored, or None when the save holds no statistics for the match.
        assists: Assists, or None when the save holds no statistics for the match. This is a
            **hypothesis**: no displayed label has been matched to this byte, and the count
            shown on a player's season statistics screen is what would confirm it
            (unconfirmed).
        rating: The match rating, which is the stored number divided by ten and so exact to one
            decimal. None when the save holds no statistics for the match, and None as well
            when the game rated nobody in it, which the save stores as a zero; `has_stats`
            tells those two apart, and the stored zero is kept as `unknown["rating_raw"]` so
            nothing is dropped. A rating is never 0.0, so an average over this column is an
            average of the ratings the game actually gave (unconfirmed).
        passes_attempted: Passes attempted, or None when the save holds no statistics for the
            match (unconfirmed).
        passes_completed: Passes completed, or None when the save holds no statistics for the
            match (unconfirmed).
        stats_in_range: fmsave's own sanity flag, not a value the save stores: true when the
            save holds this match's statistics and its minutes, rating and goals are all inside
            the bounds a match can reach. A false flag never blanks a value; every number is
            kept exactly as stored so a caller can see what the save holds (unconfirmed).
        unknown: Numeric fields with no known meaning. "role_code" moves with the position
            played but its meaning is not established, and it is absent from the mapping for a
            match the save holds no statistics for; "tag" is stored beside the date and is
            always read; "rating_raw" is the stored rating, kept only where it is zero, which
            is the one value `rating` itself cannot carry (unconfirmed).
    """

    player_uid: int
    player_name: str | None
    date: datetime.date
    competition_id: int
    opponent_team_id: int
    opponent_club_uid: int | None
    opponent_club_name: str | None
    opponent_club_short_name: str | None
    opponent_team_slot: int | None
    has_stats: bool
    position: CodedValue[MatchPosition] | None
    minutes: int | None
    left_at_minute: int | None
    goals: int | None
    assists: int | None
    rating: float | None
    passes_attempted: int | None
    passes_completed: int | None
    stats_in_range: bool
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("tag", "role_code", "rating_raw")


register_field_statuses(
    PlayerMatchStats,
    verified=(
        "date",
        "competition_id",
        "opponent_team_id",
        "opponent_club_uid",
        "opponent_club_name",
        "opponent_club_short_name",
        "position",
        "goals",
    ),
    unconfirmed=(
        "player_uid",
        "player_name",
        "opponent_team_slot",
        "has_stats",
        "minutes",
        "assists",
        "left_at_minute",
        "rating",
        "passes_attempted",
        "passes_completed",
        "stats_in_range",
        "unknown",
    ),
)
