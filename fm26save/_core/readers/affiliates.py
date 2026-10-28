"""Walking the groups of clubs in the `feeder_man` section and joining them to their clubs.

The section is a header and then variable-length groups back to back, so there is nothing to
search for: the walk starts at the layout's group offset and consumes exactly as many groups as
the header claims. It has to end on the section's last byte. That is the whole structural
check, and it is a strong one, because the only way to land on the last byte is to have read
every count in between correctly: a header read one byte out claims a group count of millions
and fails on the first group it cannot fit.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

from fm26save._core._layouts import AffiliateGroupLayout, find_layout
from fm26save._core._reader_stats import AffiliateStats
from fm26save._core.models.affiliates import AffiliateGroup
from fm26save._core.readers._common import FEEDER_SECTION, layout_mismatch
from fm26save._core.readers.clubs import ClubIndex

_UINT32 = struct.Struct("<I")


def find_affiliate_layout(schema: int | None, build: str) -> AffiliateGroupLayout:
    """Look up the affiliate-group layout for a `feeder_man` schema, falling back to the build."""
    return find_layout(AffiliateGroupLayout, FEEDER_SECTION, schema, build).layout


def _group_members_struct(member_count: int) -> struct.Struct:
    return struct.Struct(f"<{member_count}I")


def walk_affiliate_groups(
    feeder: bytes, layout: AffiliateGroupLayout, file_name: str
) -> tuple[tuple[int, ...], ...]:
    """The stored club indexes of every group, in stored order.

    Raises:
        ReaderCheckError: The section is too short to hold its header, a group's member count
            is outside the layout's cap, a group runs past the end of the section, or the walk
            does not end on the section's last byte.
    """
    lowest_size, highest_size = layout.group_size_range
    if layout.groups_offset > len(feeder):
        raise layout_mismatch(
            file_name,
            f"the section holds {len(feeder)} bytes, too few for its {layout.groups_offset}-byte "
            "header",
            section_name=FEEDER_SECTION,
        )
    (stored_group_count,) = _UINT32.unpack_from(feeder, layout.count_offset)
    cursor = layout.groups_offset
    groups: list[tuple[int, ...]] = []
    while len(groups) < stored_group_count:
        if cursor + _UINT32.size > len(feeder):
            raise layout_mismatch(
                file_name,
                f"the header claims {stored_group_count} groups and the section ends after "
                f"{len(groups)}",
                section_name=FEEDER_SECTION,
            )
        (member_count,) = _UINT32.unpack_from(feeder, cursor)
        cursor += _UINT32.size
        if not lowest_size <= member_count <= highest_size:
            raise layout_mismatch(
                file_name,
                f"group {len(groups)} claims {member_count} members, outside the "
                f"{lowest_size} to {highest_size} a group may hold",
                section_name=FEEDER_SECTION,
            )
        members_struct = _group_members_struct(member_count)
        if cursor + members_struct.size > len(feeder):
            raise layout_mismatch(
                file_name,
                f"group {len(groups)} claims {member_count} members and the section ends first",
                section_name=FEEDER_SECTION,
            )
        groups.append(members_struct.unpack_from(feeder, cursor))
        cursor += members_struct.size
    if cursor != len(feeder):
        raise layout_mismatch(
            file_name,
            f"the {stored_group_count} groups end {len(feeder) - cursor} bytes before the "
            "section does",
            section_name=FEEDER_SECTION,
        )
    return tuple(groups)


def build_affiliate_groups(
    stored_groups: Sequence[tuple[int, ...]], club_index: ClubIndex
) -> tuple[tuple[AffiliateGroup, ...], AffiliateStats]:
    """One row per stored group, with each member's stored index resolved to a club.

    A member is looked up in the public club index exactly as stored, with no offset of one:
    that is the measured index space, and an index read one higher would still resolve most
    members, so only the resolve share this counts tells the two apart. A stored index no club
    record claims leaves that member's uid and name None and is counted.
    """
    uid_for = club_index.uid_by_club_index.get
    club_for = club_index.club_by_uid.get
    groups: list[AffiliateGroup] = []
    member_count = 0
    resolved_count = 0
    for group_index, stored_members in enumerate(stored_groups):
        club_uids: list[int | None] = []
        club_names: list[str | None] = []
        for stored_member in stored_members:
            club_uid = uid_for(stored_member)
            club = None if club_uid is None else club_for(club_uid)
            club_uids.append(club_uid)
            club_names.append(None if club is None else club.name)
            member_count += 1
            if club_uid is not None:
                resolved_count += 1
        groups.append(AffiliateGroup(group_index, tuple(club_uids), tuple(club_names)))
    stats = AffiliateStats(
        groups=len(groups), members=member_count, members_resolved=resolved_count
    )
    return tuple(groups), stats
