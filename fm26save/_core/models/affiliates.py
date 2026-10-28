"""Affiliate groups: the sets of clubs the save stores together.

**What groups a set of clubs is not established.** The save stores these groups in a section of
their own, with nothing in them that says what the grouping means, and every club field here is
`unconfirmed` for that reason.

**It is not the affiliate list a club's own Affiliated Clubs screen shows.** A screen settled
that: the club whose screen listed 26 affiliates belongs to no group here at all, and the one
group naming a club that screen also names pairs that club with its own academy rather than
with the club doing the viewing. Two of that screen's rows are the parent link
`Club.parent_club_uid` already carries, and the rest are in no field fmsave reads, so neither
a club's affiliates nor the kind of each affiliation is available here.

What the grouping is remains unknown. The largest group of every save measured is recognisably
a multi-club ownership group and many two-member groups pair a club with its own lower side,
which would suit an ownership or parent-company reading, but no screen has said so and a
recognisable group is not a displayed label.

This is **not** the parent link `Club.parent_club_uid` carries. That link comes from the
affiliated-team lists inside the club records, and not one of its thousand-odd pairs is a pair
these groups hold: the two describe different relations and neither is derived from the other.
"""

from __future__ import annotations

from dataclasses import dataclass

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class AffiliateGroup:
    """One stored group of clubs, with its members resolved to clubs where they resolve.

    Attributes:
        group_index: The group's own place in the section, counting from zero in stored
            order. It is fmsave's own index and not a value the save keeps: the groups carry
            no id of their own.
        club_uids: Uid of each member, in stored order, None for a member whose stored club
            index no club record claims, which is about one member in sixty (unconfirmed).
        club_names: Denormalised full name of each entry of `club_uids`, aligned with it and
            None wherever that uid is (unconfirmed).
    """

    group_index: int
    club_uids: tuple[int | None, ...]
    club_names: tuple[str | None, ...]


# The index is fmsave's own position in the section, which is structural. What the group means
# is not: one screen has ruled out the affiliate list and named nothing in its place, so the
# members and their names stay unconfirmed until a screen names a grouping.
register_field_statuses(
    AffiliateGroup,
    verified=("group_index",),
    unconfirmed=("club_uids", "club_names"),
)
