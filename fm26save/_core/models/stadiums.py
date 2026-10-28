"""Stadiums: every ground the save's database holds, and the clubs that play at them.

The save stores a ground's capacities, its pitch, when it was built and rebuilt, and which
club owns it. It stores **no pointer from a club to the ground it plays at**, so the only
honest link is the one the fixture calendar gives: the ground a club actually plays its home
matches at, which is what `home_club_uids` holds. Ownership and use are different things, and
the table carries both separately.

Most grounds have no name here. The game takes a ground's name from its installed database,
and only a couple of hundred rows of a save's table carry one inline, so `name` is empty on
nearly every row.

The table's closing object header marks the end of its ground records and is not returned as
a ground.

Derived views the table carries no field for:

- the ground a club plays at is `stadiums().filter(lambda stadium: club_uid in
  stadium.home_club_uids)`;
- the grounds a club owns are `stadiums().where(owner_club_uid=club_uid)`.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class Stadium:
    """One ground the save's database holds.

    Attributes:
        uid: The ground's uid, which is the stored value plus one, the same convention club
            uids follow. A stadium uid that equals a club uid is a coincidence: the two are
            separate id spaces and must never be joined on (unconfirmed).
        name: The ground's name as the save stores it inline, or None when the save stores
            none, which is the case for nearly every ground: the game takes the name from its
            installed database instead (unconfirmed).
        all_seater_capacity: How many seated spectators the ground holds.
        expansion_capacity: The capacity the ground would hold expanded, which is at or above
            the all-seater capacity on all but a handful of grounds.
        capacity: A further capacity the save stores, empty where the save stores zero, which
            is about four grounds in five (unconfirmed).
        owner_club_uid: Uid of the club that owns the ground, or None when the save names no
            owner or names a club it does not list. A ground with no stored owner is the
            council's: the game's own facilities screen shows one such ground as owned by the
            council, so an empty owner is an answer rather than a gap. Owning a ground is not
            the same as playing at it (unconfirmed).
        owner_club_name: Denormalised name of owner_club_uid, or None when there is no owner
            or the owner does not resolve (unconfirmed).
        home_club_uids: Uids of the clubs whose home ground this is, in ascending order. It
            comes from the fixture calendar, not from any stored link: a club has a home
            ground once the calendar records enough first-team home matches for it, and that
            ground is the one it used most. It is empty for a ground no club uses often
            enough, and a ground several clubs share lists each of them (unconfirmed).
        home_club_names: Denormalised names of home_club_uids, in the same order
            (unconfirmed).
        pitch_length_dm: The pitch's length in decimetres.
        pitch_width_dm: The pitch's width in decimetres.
        pitch_min_length_dm: The shortest pitch length the ground allows (unconfirmed).
        pitch_min_width_dm: The narrowest pitch width the ground allows (unconfirmed).
        pitch_max_length_dm: The longest pitch length the ground allows.
        pitch_max_width_dm: The widest pitch width the ground allows.
        built_date: The date the ground was built, or None when the save stores none. A few
            grounds carry a date after the save's own clock.
        rebuilt_date: The date the ground was last rebuilt, or None when the save stores none.
        unknown: Numeric fields with no known meaning: two capacity-like words, a small code,
            a third date as one little-endian int, and the whole flags byte whose 0x10 bit is
            what says the row carries its name inline (unconfirmed).
    """

    uid: int
    name: str | None
    all_seater_capacity: int
    expansion_capacity: int
    capacity: int | None
    owner_club_uid: int | None
    owner_club_name: str | None
    home_club_uids: tuple[int, ...]
    home_club_names: tuple[str, ...]
    pitch_length_dm: int
    pitch_width_dm: int
    pitch_min_length_dm: int
    pitch_min_width_dm: int
    pitch_max_length_dm: int
    pitch_max_width_dm: int
    built_date: datetime.date | None
    rebuilt_date: datetime.date | None
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("u17", "u25", "b33", "date_58", "flags_156")


# The capacities, the pitch and the two dates are the fields an independent read of these
# saves confirms one by one, and two grounds' own facilities screens showed each of them, the
# maximum pitch dimensions included, in yards against the stored decimetres. The uid
# convention, the owner's id space, the smallest pitch a ground allows and the
# calendar-derived home grounds are measured rather than displayed anywhere, so they stay
# unconfirmed until an in-game screen names one.
register_field_statuses(
    Stadium,
    verified=(
        "all_seater_capacity",
        "expansion_capacity",
        "pitch_length_dm",
        "pitch_width_dm",
        "pitch_max_length_dm",
        "pitch_max_width_dm",
        "built_date",
        "rebuilt_date",
    ),
    unconfirmed=(
        "uid",
        "name",
        "capacity",
        "owner_club_uid",
        "owner_club_name",
        "home_club_uids",
        "home_club_names",
        "pitch_min_length_dm",
        "pitch_min_width_dm",
        "unknown",
    ),
)
