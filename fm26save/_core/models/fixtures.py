"""Matches recovered from the save's fixture calendar.

A fixture joins to its competition through its **stage**, so `competition_id` here belongs to
the stage id space shared by `Suspension.competition_id` and the league tables. A stage the stage table does not hold leaves the
competition fields empty rather than guessing them.

The save stores no competition name, so `competition_name` is None unless a name map was
supplied to `fmsave.open`, and then only for competitions whose editor database id resolves.

Derived views the calendar carries no field for:

- a club's own fixture list is `where(home_club_uid=...)` or `where(away_club_uid=...)`, or
  `filter(...)` for both at once; the home and away fields then say which side it was;
- a matchday is `round_index + 1`, since the stored index counts from zero;
- a season by date uses a 1 July boundary, which is not the same as `season_start_year`: that
  field is what the record stores, and it is None on some friendlies;
- a youth or reserve side is `away_club_short_name` together with `away_team_slot`. fmsave
  never builds a localised "B team" or "U21" name of its own, because the save holds none.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue
from fm26save._core.models.competitions import CompetitionRound


@dataclass(frozen=True, slots=True)
class Fixture:
    """One match in the save's fixture calendar.

    Attributes:
        stage_id: The stage this match belongs to, which is the only route to its
            competition; None when the record stores no stage.
        competition_id: Id of the competition, in the **stage** id space, reached through the stage;
            None when the
            record has no stage, the stage is not in the stage table, or the stage names no
            competition.
        competition_name: Denormalised name of competition_id, which is None unless a name
            map is supplied, because the save stores no competition names (unconfirmed).
        round: The stage's round, or None when the match has no stage or its stage carries no
            round, as a league matchday and a league phase do not. Codes with no confirmed
            meaning keep their raw number and are labelled UNKNOWN.
        round_index: The match's zero-based index within its round, so a matchday is this
            plus one; None when the record stores the no-round value.
        date: The kick-off date, or None when the stored date does not decode.
        kick_off_time: The kick-off time of day, or None when the stored slot does not land
            inside a day.
        season_start_year: The calendar year the season started in, or None when the record
            stores none, as some friendlies do.
        home_team_id: The home side's team id, exactly as stored.
        home_club_uid: Uid of the club fielding the home team, or None when no club lists
            that team.
        home_club_name: Denormalised name of home_club_uid, or None when the team does not
            resolve.
        home_club_short_name: Denormalised short name of home_club_uid, or None when the team
            does not resolve.
        home_team_slot: The home team's slot in its club's team list, 0 for the first entry,
            or None when the team does not resolve.
        away_team_id: The away side's team id, exactly as stored.
        away_club_uid: Uid of the club fielding the away team, or None when no club lists
            that team.
        away_club_name: Denormalised name of away_club_uid, or None when the team does not
            resolve.
        away_club_short_name: Denormalised short name of away_club_uid, or None when the team
            does not resolve.
        away_team_slot: The away team's slot in its club's team list, 0 for the first entry,
            or None when the team does not resolve.
        home_goals: Goals the home side scored, or None when no unambiguous score was
            decoded. Empty goals on a played match do not mean it finished goalless.
            Score coverage varies between saves.
        away_goals: Goals the away side scored, or None when no unambiguous score was
            decoded, as for home_goals.
        played: Whether the save marks the match as played.
        is_neutral_venue: Whether the match was played away from the home club's usual
            ground: True when its ground differs from the one that club used most in this
            season, False when it matches, and None when the ground is unknown or the club
            played too few home matches this season to say which ground is usual. This is
            about the ground and not about which club counts as the home one: the home club is
            `home_team_id` whether the ground is neutral or not, and
            `LeagueTableMatch.home_or_away` is the field that says which side of a match a club
            was. The season
            is the stored season_start_year, which some friendlies leave empty, and every
            such match a club played shares one vote; a club that moved ground mid-career
            therefore has its earlier seasonless matches judged against the later ground.
        stadium_uid: Uid of the ground the match is played at, from the stadium table; None
            when the record stores no ground or one the table does not hold. The join itself
            is exact, but a stadium uid is not confirmed by any displayed label, so this field
            can be no stronger than the uid it carries (unconfirmed).
        stadium_name: Denormalised name of stadium_uid. Only a couple of hundred grounds
            store a name, so this is None on nearly every match even where stadium_uid is
            filled in; `Stadium.name` says why (unconfirmed).
        match_record_id: Id of the match record the save keeps for a played match, or None
            when the match is unplayed (unconfirmed).
        match_rules_template: The three bytes naming the shared match-rules template this
            match uses. It is a template many competitions share and is **never** a
            competition id (unconfirmed).
        unknown: Numeric fields with no known meaning. "result_r22" is the byte stored beside
            a stage-keyed result. A score recovered only from a match summary or calendar
            packet carries no such byte (unconfirmed).
    """

    stage_id: int | None
    competition_id: int | None
    competition_name: str | None
    round: CodedValue[CompetitionRound] | None
    round_index: int | None
    date: datetime.date | None
    kick_off_time: datetime.time | None
    season_start_year: int | None
    home_team_id: int
    home_club_uid: int | None
    home_club_name: str | None
    home_club_short_name: str | None
    home_team_slot: int | None
    away_team_id: int
    away_club_uid: int | None
    away_club_name: str | None
    away_club_short_name: str | None
    away_team_slot: int | None
    home_goals: int | None
    away_goals: int | None
    played: bool
    is_neutral_venue: bool | None
    stadium_uid: int | None
    stadium_name: str | None
    match_record_id: int | None
    match_rules_template: tuple[int, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = (
        "date2",
        "phase",
        "leg",
        "r39_42",
        "r47_54",
        "result_r22",
    )


register_field_statuses(
    Fixture,
    verified=(
        "stage_id",
        "competition_id",
        "round",
        "round_index",
        "date",
        "kick_off_time",
        "season_start_year",
        "home_team_id",
        "home_club_uid",
        "home_club_name",
        "home_club_short_name",
        "home_team_slot",
        "away_team_id",
        "away_club_uid",
        "away_club_name",
        "away_club_short_name",
        "away_team_slot",
        "home_goals",
        "away_goals",
        "played",
        "is_neutral_venue",
    ),
    # `stadium_uid` is a derived field and takes the weaker of its inputs: the ordinal it joins
    # on resolves exactly, but `Stadium.uid` is unconfirmed, so this cannot be verified.
    unconfirmed=(
        "competition_name",
        "stadium_uid",
        "stadium_name",
        "match_record_id",
        "match_rules_template",
        "unknown",
    ),
)
