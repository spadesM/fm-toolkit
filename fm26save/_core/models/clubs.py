"""Clubs and the teams they field."""

from __future__ import annotations

from dataclasses import dataclass

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class Team:
    """One team in a club's team list.

    A club's team list holds its own stored team slots, in stored order, then the teams it
    fields at the clubs it controls, such as a B or C team stored as a club of its own.

    Attributes:
        team_id: The team's id, which player records use to name their team (unconfirmed).
        slot: Position in the club's team list, 0 for the first entry. Which side each own
            slot holds, such as a reserve or youth team, is not known (unconfirmed).
        club_uid: Uid of the club whose record stores this team: the club listing it for its
            own teams, and the affiliate club itself for an affiliate team (unconfirmed).
        is_affiliate: Whether the team belongs to an affiliate club the listing club controls
            (unconfirmed).
    """

    team_id: int
    slot: int
    club_uid: int
    is_affiliate: bool


@dataclass(frozen=True, slots=True)
class Club:
    """A club from the save's game database.

    Club names are not unique: look clubs up by uid.

    Attributes:
        uid: The id other records in this save use to refer to this club. It can differ
            between separate careers, so use unique_id to match clubs across saves
            (unconfirmed).
        name: Full club name (unconfirmed).
        short_name: Short club name (unconfirmed).
        nation_id: Id of the nation whose league the club plays in (unconfirmed).
        fa_nation_id: Id of the nation whose football association the club belongs to. It
            differs from nation_id for a club that plays in another nation's league
            (unconfirmed).
        city_id: Id of the club's city, or None when the save stores the missing-id marker
            instead (unconfirmed).
        teams: The club's own teams in stored order, including slots no player is registered
            with, then the teams of the affiliate clubs it controls; an empty tuple when the
            team list cannot be read (unconfirmed).
        parent_club_uid: Uid of the club that controls this one, when another club lists one
            of this club's teams among its affiliate teams, else None (unconfirmed).
        parent_club_name: Denormalised full name of parent_club_uid; None wherever
            parent_club_uid is (unconfirmed).
        reputation: Club reputation from 1 to 10000, or None when the save holds no valid
            value.
        last_league_position: League position at the end of the last completed season, or
            None when the save holds none. It is not the position in the current table.
        unique_id: The club's Unique ID in the game database, for matching across separate
            careers. None when it cannot be read (unconfirmed).
    """

    uid: int
    name: str
    short_name: str
    nation_id: int
    fa_nation_id: int
    city_id: int | None
    teams: tuple[Team, ...]
    parent_club_uid: int | None
    parent_club_name: str | None
    reputation: int | None
    last_league_position: int | None
    unique_id: int | None = None


register_field_statuses(Team, unconfirmed=("team_id", "slot", "club_uid", "is_affiliate"))
register_field_statuses(
    Club,
    verified=("reputation", "last_league_position"),
    unconfirmed=(
        "uid",
        "unique_id",
        "name",
        "short_name",
        "nation_id",
        "fa_nation_id",
        "city_id",
        "teams",
        "parent_club_uid",
        "parent_club_name",
    ),
)
