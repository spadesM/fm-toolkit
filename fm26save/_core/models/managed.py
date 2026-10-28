"""Clubs managed by the save's human managers."""

from __future__ import annotations

from dataclasses import dataclass

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class ManagedClub:
    """A club run by one of the save's human managers.

    The link from a human manager to a club is proven only on saves with a single human
    manager. On a save with several human managers, only the first one may be listed. A
    manager with no current club, for example one between jobs, has no row.

    Attributes:
        club_uid: Uid of the managed club (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        club_short_name: Denormalised short name of club_uid (unconfirmed).
        manager_name: The human manager's name as the save summary stores it, or None when
            the summary does not name the manager next to the club (unconfirmed).
        manager_staff_uid: Uid of the human manager's own record, which is a `Staff.uid`
            and joins to the staff table; None when it cannot be identified exactly.
            manager_name is this person's name (unconfirmed).
    """

    club_uid: int
    club_name: str
    club_short_name: str
    manager_name: str | None
    manager_staff_uid: int | None


register_field_statuses(
    ManagedClub,
    unconfirmed=(
        "club_uid",
        "club_name",
        "club_short_name",
        "manager_name",
        "manager_staff_uid",
    ),
)
