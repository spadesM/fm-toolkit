"""Unserved suspensions: bans a player has been given and has not yet served.

The save keeps a player's suspension only while it is unserved. Every unserved ban it holds is
listed here, including bans the game no longer displays; the save stores no flag that tells
those apart, and why the game stops displaying one is not confirmed.

A ban stores one id and one scope code that says what the id refers to. A ban on one
competition stores a competition id in the **stage** id space, the same space `stages()`,
`competitions()`, `fixtures()`, `league_tables()` and `player_match_stats()` use, so it joins
to all of them. A nation-wide ban stores a **nation** id instead. The two are told apart here
rather than by the caller: `competition_id` is None on a nation-wide ban and `nation_id` is
None on a ban covering one competition, so neither can be read as the other.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses


class SuspensionScope(StrEnum):
    """What a ban covers, and so what the id the save stores beside it refers to.

    The save writes one code per ban. Code 1 means the ban covers the one competition its id
    names; codes 5, 6 and 10 mean the ban covers every competition of the nation its id names.
    Any other code reads as UNKNOWN, and a ban with an unknown code carries no competition id
    and no nation id, because nothing says which the stored number is.

    What separates codes 5, 6 and 10 from one another is not known; all three were measured to
    carry a nation id, so all three read as NATION and `Suspension.scope_code` keeps the code
    itself for a caller who wants to tell them apart.
    """

    COMPETITION = "competition"
    NATION = "nation"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PlayerSuspension:
    """One unserved suspension, as listed on its player.

    Attributes:
        scope: What the ban covers: one competition, a whole nation, or UNKNOWN for a scope
            code never measured.
        scope_code: The scope code exactly as the save stores it: 1 for a competition-wide
            ban, 5, 6 or 10 for a nation-wide one. What separates 5, 6 and 10 is not known.
        competition_id: Id of the competition the ban applies to, in the **stage** id space,
            so it joins `stages()`, `competitions()`, `fixtures()`, `league_tables()` and
            `player_match_stats()`. None unless the scope is COMPETITION.
        competition_name: Denormalised name of competition_id, which is None unless a name
            map is supplied, because the save stores no competition names. A competition the
            game itself created during the career has a database id no name source outside
            the save carries, so some rows stay unnamed even with a full map (unconfirmed).
        nation_id: Id of the nation whose competitions the ban covers, in the same id space
            as `Club.nation_id` and `Player.nation_id`. None unless the scope is NATION.
        issued_date: Date the ban was issued.
    """

    scope: SuspensionScope
    scope_code: int
    competition_id: int | None
    competition_name: str | None
    nation_id: int | None
    issued_date: date


@dataclass(frozen=True, slots=True)
class Suspension:
    """One unserved suspension, with its player and the club the player belongs to.

    A ban the game no longer displays is listed here too.

    Attributes:
        player_uid: Uid of the suspended player, copied from the decoded player
            (unconfirmed).
        player_name: Denormalised name of player_uid (unconfirmed).
        club_uid: Uid of the club the player belongs to, which for a player registered with
            a team another club controls is that controlling club; None for a free agent or
            a team that does not resolve to a club. Copied from the decoded player
            (unconfirmed). It is the club the player belongs to **now**, which for an old
            ban need not be the club he was banned at.
        club_name: Denormalised full name of club_uid (unconfirmed).
        scope: What the ban covers: one competition, a whole nation, or UNKNOWN for a scope
            code never measured.
        scope_code: The scope code exactly as the save stores it: 1 for a competition-wide
            ban, 5, 6 or 10 for a nation-wide one. What separates 5, 6 and 10 is not known.
        competition_id: Id of the competition the ban applies to, in the **stage** id space,
            so it joins `stages()`, `competitions()`, `fixtures()`, `league_tables()` and
            `player_match_stats()`. None unless the scope is COMPETITION.
        competition_name: Denormalised name of competition_id, which is None unless a name
            map is supplied, because the save stores no competition names. A competition the
            game itself created during the career has a database id no name source outside
            the save carries, so some rows stay unnamed even with a full map (unconfirmed).
        nation_id: Id of the nation whose competitions the ban covers, in the same id space
            as `Club.nation_id` and `Player.nation_id`. None unless the scope is NATION.
        issued_date: Date the ban was issued.
        unknown: Numeric fields with no known meaning (unconfirmed).
    """

    player_uid: int
    player_name: str | None
    club_uid: int | None
    club_name: str | None
    scope: SuspensionScope
    scope_code: int
    competition_id: int | None
    competition_name: str | None
    nation_id: int | None
    issued_date: date
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("e7",)


# scope, scope_code, competition_id and nation_id are verified together, because one
# measurement over several saves settles all four. Every ban whose scope code is 1 stores a
# number the save's own competition table holds, and wherever the fixture calendar can test
# it, the player's club played that very competition on the day the ban was issued - against
# a shuffled control that scores near nothing, and with every exception a ban old enough for
# the player to have changed club since. A ban whose code is 5, 6 or 10 never passes that
# test and instead stores a nation the player or his club holds, which no code-1 ban ever
# does. So the code selects the id space, and neither reading survives being applied to the
# other group. What separates codes 5, 6 and 10 from one another is still unmeasured, which
# is why the code itself ships beside the scope.
register_field_statuses(
    PlayerSuspension,
    verified=("scope", "scope_code", "competition_id", "nation_id", "issued_date"),
    unconfirmed=("competition_name",),
)
# player_uid, club_uid and club_name are copies of Player fields, so they carry the status of
# the fields they are copied from rather than a stronger one of their own.
register_field_statuses(
    Suspension,
    verified=("scope", "scope_code", "competition_id", "nation_id", "issued_date"),
    unconfirmed=(
        "player_uid",
        "player_name",
        "club_uid",
        "club_name",
        "competition_name",
        "unknown",
    ),
)
