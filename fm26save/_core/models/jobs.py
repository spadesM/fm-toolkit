"""Open jobs: the vacancies the save's job-centre feed holds.

**The feed keeps old rows.** The earliest advertised date on the saves measured is about ten
years before the in-game date, so a row here is a vacancy the save still remembers rather than
one the game would list today. Nothing in a row says whether it has been filled.

A vacancy is keyed on a team rather than a club, so `team_id` is what the save stores and the
club fields come from the club that fields that team. A row's role, its second date and two
further numbers have no confirmed meaning and ship in `unknown`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class JobVacancy:
    """One job the save's job-centre feed holds.

    Attributes:
        team_id: The team the job is at, None where the record names no team.
        club_uid: Uid of the club that fields `team_id`, None for a team no club lists and
            wherever team_id is.
        club_name: Denormalised full name of club_uid, None wherever club_uid is.
        team_slot: The team's place in that club's own team list, 0 for its first team;
            None when the team resolves to no club (unconfirmed).
        advertised_date: Date the vacancy was advertised, None when the stored date does not
            decode. The time of day the save stores with it is in `unknown["advertised_slot"]`.
        competition_id: Id of the competition the job's team plays in, in the stage id space;
            None where the record names none (unconfirmed).
        competition_name: Denormalised name of competition_id, None unless the save was
            opened with a name map that names it (unconfirmed).
        league_position: The team's current position in that competition's table, None where
            the record stores none, which is about a quarter of rows (unconfirmed).
        unknown: Numeric fields with no known meaning: the role code the vacancy's job title
            comes from, the advertised date's time-of-day slot, a second date whose meaning is
            not settled (its raw four bytes as one little-endian int, not a decoded date), an
            attribute of the competition, and a 0/1 flag (unconfirmed).
    """

    team_id: int | None
    club_uid: int | None
    club_name: str | None
    team_slot: int | None
    advertised_date: date | None
    competition_id: int | None
    competition_name: str | None
    league_position: int | None
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("role", "advertised_slot", "date_12", "u20", "b24")


# The team key, the club join and the advertised date are each pinned by a measurement that
# separates them from every neighbouring offset. The competition link and the league position
# agree with the stage table and the live tables but no screen has named either, so both stay
# unconfirmed along with everything in `unknown`. `team_slot` is the place a team takes in a
# club's own list, which is counted rather than displayed; every other table that ships it
# reads it from the same map and calls it unconfirmed, and so does this one.
register_field_statuses(
    JobVacancy,
    verified=("team_id", "club_uid", "club_name", "advertised_date"),
    unconfirmed=(
        "team_slot",
        "competition_id",
        "competition_name",
        "league_position",
        "unknown",
    ),
)
