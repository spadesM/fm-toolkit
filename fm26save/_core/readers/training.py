"""Walking the team blocks of the `training_man` section, and finding the schedule library.

The section is a per-person header list, then one variable-length block per team of the club
the save's manager runs, then tens of kilobytes of other data. Nothing is searched for to
reach a block: the header list's own count says where the first one starts, and each block
ends where its mentoring groups do. What ends the walk is the blocks running out, which the
save marks by following the last one with bytes that are not another block of a team of that
club, so the check on the walk is that it found exactly as many blocks as the club has teams.
Starting one byte or four bytes late parses no block at all.

Inside a block the calendar is the part worth being careful about. Each weekly record is a
lead byte, **the week's own start date**, seven day blocks of session codes, the schedule
name, and fourteen further bytes, so the record's length is 73 plus the name's. That length was
measured record by record against the next record's lead byte on every save: read four bytes
short, a record ends inside the next one, and the walk falls apart rather than quietly pairing
each name with the following week.

The library of saved schedules sits after the last block at no fixed distance, so it is the one
thing here found by shape: the run of bytes that precedes a group's entry count, followed by
entries that all decode. Nothing looks at any text to find it, and a section holding no such
run simply has no library.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from itertools import pairwise

from fm26save._core._errors import CorruptSaveError
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import TrainingLayout, find_layout
from fm26save._core._reader_stats import TrainingStats
from fm26save._core._scan import decode_date, find_marker, read_length_prefixed_string
from fm26save._core.models.players import Player
from fm26save._core.models.training import MentoringGroup, TeamTraining, TrainingSchedule, TrainingWeek
from fm26save._core.readers._common import TRAINING_SECTION, layout_mismatch
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.player_scan import PlayerRecords
from fm26save._core.table import Table

_UINT32 = struct.Struct("<I")


def find_training_layout(schema: int | None, build: str) -> TrainingLayout:
    """Look up the training layout for a `training_man` schema, falling back to the build."""
    return find_layout(TrainingLayout, TRAINING_SECTION, schema, build).layout


@dataclass(frozen=True, slots=True)
class RawTrainingBlock:
    """One team's block as the section stores it, before any club or player join.

    `groups` holds one `(group number, label, member selectors)` per mentoring group, with the
    selectors exactly as stored: each is a player's record index plus one.
    """

    team_id: int
    weeks: tuple[TrainingWeek, ...]
    groups: tuple[tuple[int, str, tuple[int, ...]], ...]


@dataclass(frozen=True, slots=True)
class TrainingWalkCounts:
    """What the block walk counted, and where it stopped.

    `week_steps` counts the moves from one week of a block to the next where both weeks carry
    a date, and `seven_day_steps` those that stepped exactly a week. `blocks_end` is the offset
    the walk stopped at, which is where the search for the schedule library starts.
    """

    header_entries: int
    weeks: int
    week_steps: int
    seven_day_steps: int
    undated_weeks: int
    blocks_end: int


def _short_section_error(section_bytes: int, header_entries: int, file_name: str) -> Exception:
    return layout_mismatch(
        file_name,
        f"the section holds {section_bytes} bytes, too few for the {header_entries} header "
        "entries it claims and a team block after them",
        section_name=TRAINING_SECTION,
    )


def _read_word(section: bytes, offset: int, what: str, file_name: str) -> int:
    if offset < 0 or offset + _UINT32.size > len(section):
        raise layout_mismatch(
            file_name,
            f"the section ends before {what}",
            section_name=TRAINING_SECTION,
        )
    return _UINT32.unpack_from(section, offset)[0]


def _read_text(
    section: bytes, offset: int, longest: int, what: str, file_name: str
) -> tuple[str, int]:
    try:
        return read_length_prefixed_string(section, offset, longest)
    except CorruptSaveError as error:
        raise layout_mismatch(
            file_name, f"{what} does not read as stored text", section_name=TRAINING_SECTION
        ) from error


def _read_week(
    section: bytes, cursor: int, layout: TrainingLayout, file_name: str
) -> tuple[TrainingWeek, int]:
    """One weekly record, and the offset just past it."""
    if cursor + layout.week_name_offset + _UINT32.size > len(section):
        raise layout_mismatch(
            file_name,
            "a weekly record runs past the end of the section",
            section_name=TRAINING_SECTION,
        )
    if section[cursor] != layout.week_lead_byte:
        raise layout_mismatch(
            file_name,
            f"a weekly record starts with {section[cursor]:#04x} rather than "
            f"{layout.week_lead_byte:#04x}",
            section_name=TRAINING_SECTION,
        )
    if section[cursor + layout.week_marker_offset] != layout.week_marker_value:
        raise layout_mismatch(
            file_name,
            "a weekly record does not carry its marker byte",
            section_name=TRAINING_SECTION,
        )
    for day_index in range(layout.day_block_count):
        day_offset = cursor + layout.day_blocks_offset + day_index * layout.day_block_bytes
        if section[day_offset] != layout.day_block_lead_byte:
            raise layout_mismatch(
                file_name,
                f"day {day_index} of a weekly record does not carry its lead byte",
                section_name=TRAINING_SECTION,
            )
    schedule_name, name_end = _read_text(
        section,
        cursor + layout.week_name_offset,
        layout.longest_name_bytes,
        "a schedule name",
        file_name,
    )
    # The name's own end is what the trailer is counted from, so the record's length has one
    # source of truth: the length the save stored, not that length worked out again.
    record_end = name_end + layout.week_trailer_bytes
    if record_end > len(section):
        raise layout_mismatch(
            file_name,
            "a weekly record's trailer runs past the end of the section",
            section_name=TRAINING_SECTION,
        )
    week_start = decode_date(section, cursor + layout.week_date_offset)
    return TrainingWeek(week_start, schedule_name), record_end


def _read_group(
    section: bytes, cursor: int, layout: TrainingLayout, file_name: str
) -> tuple[tuple[int, str, tuple[int, ...]], int]:
    """One mentoring group, and the offset just past it."""
    if cursor + 6 > len(section):
        raise layout_mismatch(
            file_name,
            "a mentoring group runs past the end of the section",
            section_name=TRAINING_SECTION,
        )
    if section[cursor] != layout.group_lead_byte:
        raise layout_mismatch(
            file_name,
            f"a mentoring group starts with {section[cursor]:#04x} rather than "
            f"{layout.group_lead_byte:#04x}",
            section_name=TRAINING_SECTION,
        )
    group_number = _read_word(section, cursor + 1, "a mentoring group's number", file_name)
    label_marker_offset = cursor + 1 + _UINT32.size
    if section[label_marker_offset] != layout.group_label_marker:
        raise layout_mismatch(
            file_name,
            "a mentoring group does not carry its label marker",
            section_name=TRAINING_SECTION,
        )
    label, after_label = _read_text(
        section,
        label_marker_offset + 1,
        layout.longest_name_bytes,
        "a mentoring group's label",
        file_name,
    )
    member_count = _read_word(section, after_label, "a mentoring group's member count", file_name)
    if member_count > layout.most_members_per_group:
        raise layout_mismatch(
            file_name,
            f"a mentoring group claims {member_count} members, more than the "
            f"{layout.most_members_per_group} a group may hold",
            section_name=TRAINING_SECTION,
        )
    members_offset = after_label + _UINT32.size
    members_bytes = member_count * _UINT32.size
    if members_offset + members_bytes > len(section):
        raise layout_mismatch(
            file_name,
            f"a mentoring group claims {member_count} members and the section ends first",
            section_name=TRAINING_SECTION,
        )
    members = struct.unpack_from(f"<{member_count}I", section, members_offset)
    return (group_number, label, members), members_offset + members_bytes


def _block_starts_here(
    section: bytes, cursor: int, club_team_ids: frozenset[int], seen_team_ids: set[int]
) -> int | None:
    """The team id of the block at `cursor`, or None when no block of the club starts there."""
    if cursor < 0 or cursor + _UINT32.size > len(section):
        return None
    team_id: int = _UINT32.unpack_from(section, cursor)[0]
    if team_id not in club_team_ids or team_id in seen_team_ids:
        return None
    return team_id


def walk_training_blocks(
    section: bytes, club_team_ids: frozenset[int], layout: TrainingLayout, file_name: str
) -> tuple[tuple[RawTrainingBlock, ...], TrainingWalkCounts]:
    """Every team block the section holds, in stored order, with what the walk counted.

    The walk stops as soon as the bytes at the cursor are not a block of a team of the managed
    club it has not already read, which is how the last block is recognised: no count says how
    many blocks there are. A block it has committed to and then cannot read is a layout that
    has moved, and raises.

    Raises:
        ReaderCheckError: The section is too short to hold its header list, or a block the walk
            accepted holds a weekly record or a mentoring group it cannot read: a lead byte, a
            marker, a name, a count outside its cap, or a part running past the end.
    """
    header_entries = _read_word(
        section, layout.header_count_offset, "its header entry count", file_name
    )
    blocks_offset = (
        layout.header_list_offset
        + layout.header_entry_bytes * header_entries
        + layout.header_gap_bytes
    )
    if blocks_offset > len(section):
        raise _short_section_error(len(section), header_entries, file_name)
    blocks: list[RawTrainingBlock] = []
    seen_team_ids: set[int] = set()
    blocks_end = blocks_offset
    week_count = 0
    week_steps = 0
    seven_day_steps = 0
    undated_weeks = 0
    cursor = blocks_offset
    while True:
        team_id = _block_starts_here(section, cursor, club_team_ids, seen_team_ids)
        if team_id is None:
            break
        lead_offset = cursor + _UINT32.size
        if lead_offset >= len(section) or section[lead_offset] != layout.block_lead_byte:
            break
        entry_count = _read_word(section, lead_offset + 1, "a block's entry count", file_name)
        entries_offset = lead_offset + 1 + _UINT32.size
        weeks_count_offset = entries_offset + entry_count * layout.block_entry_bytes
        if weeks_count_offset + _UINT32.size > len(section):
            raise layout_mismatch(
                file_name,
                f"a block claims {entry_count} entries and the section ends first",
                section_name=TRAINING_SECTION,
            )
        for entry_index in range(entry_count):
            entry_offset = entries_offset + entry_index * layout.block_entry_bytes
            if section[entry_offset] != layout.block_entry_lead_byte:
                raise layout_mismatch(
                    file_name,
                    f"entry {entry_index} of a block does not carry its lead byte",
                    section_name=TRAINING_SECTION,
                )
        stored_week_count = _read_word(
            section, weeks_count_offset, "a block's week count", file_name
        )
        weeks: list[TrainingWeek] = []
        position = weeks_count_offset + _UINT32.size
        for _week_index in range(stored_week_count):
            week, position = _read_week(section, position, layout, file_name)
            weeks.append(week)
        group_count_offset = position + layout.block_tail_bytes
        stored_group_count = _read_word(
            section, group_count_offset, "a block's mentoring group count", file_name
        )
        groups: list[tuple[int, str, tuple[int, ...]]] = []
        position = group_count_offset + _UINT32.size
        for _group_index in range(stored_group_count):
            group, position = _read_group(section, position, layout, file_name)
            groups.append(group)
        seen_team_ids.add(team_id)
        blocks.append(RawTrainingBlock(team_id, tuple(weeks), tuple(groups)))
        blocks_end = position
        week_count += len(weeks)
        undated_weeks += sum(1 for week in weeks if week.week_start is None)
        for earlier, later in pairwise(weeks):
            if earlier.week_start is None or later.week_start is None:
                continue
            week_steps += 1
            if later.week_start - earlier.week_start == timedelta(days=layout.seven_day_step):
                seven_day_steps += 1
        if position >= len(section) or section[position] != layout.block_terminator:
            break
        cursor = position + 1
    counts = TrainingWalkCounts(
        header_entries=header_entries,
        weeks=week_count,
        week_steps=week_steps,
        seven_day_steps=seven_day_steps,
        undated_weeks=undated_weeks,
        blocks_end=blocks_end,
    )
    return tuple(blocks), counts


def _optional_text(section: bytes, offset: int, longest: int) -> tuple[str, int] | None:
    try:
        text, text_end = read_length_prefixed_string(section, offset, longest)
    except CorruptSaveError:
        return None
    return (text, text_end) if text else None


def _library_entry(
    section: bytes, cursor: int, layout: TrainingLayout
) -> tuple[TrainingSchedule, int] | None:
    """One saved schedule and the offset past it, or None when no entry starts at `cursor`."""
    folder_offset = cursor + layout.library_folder_offset
    if folder_offset + _UINT32.size > len(section):
        return None
    if section[cursor] != layout.library_entry_lead_byte:
        return None
    stored_word: int = _UINT32.unpack_from(section, cursor + layout.library_entry_word_offset)[0]
    if stored_word != layout.library_entry_word_value:
        return None
    if section[cursor + layout.library_entry_marker_offset] != layout.library_entry_marker_value:
        return None
    for day_index in range(layout.day_block_count):
        day_offset = cursor + layout.library_day_blocks_offset + day_index * layout.day_block_bytes
        if section[day_offset] != layout.day_block_lead_byte:
            return None
    read_folder = _optional_text(section, folder_offset, layout.longest_name_bytes)
    if read_folder is None:
        return None
    folder, after_folder = read_folder
    if after_folder + _UINT32.size > len(section):
        return None
    schedule_id: int = _UINT32.unpack_from(section, after_folder)[0]
    read_name = _optional_text(section, after_folder + _UINT32.size, layout.longest_name_bytes)
    if read_name is None:
        return None
    name, after_name = read_name
    unknown: Mapping[str, int] = FrozenMapping({"schedule_id": schedule_id})
    return TrainingSchedule(folder, name, unknown), after_name


def _library_group(
    section: bytes, cursor: int, layout: TrainingLayout
) -> tuple[tuple[TrainingSchedule, ...], int] | None:
    """One count-prefixed group of saved schedules, or None when none starts at `cursor`."""
    if cursor + _UINT32.size > len(section):
        return None
    entry_count: int = _UINT32.unpack_from(section, cursor)[0]
    if entry_count > layout.most_library_entries:
        return None
    schedules: list[TrainingSchedule] = []
    position = cursor + _UINT32.size
    for _entry_index in range(entry_count):
        read_entry = _library_entry(section, position, layout)
        if read_entry is None:
            return None
        schedule, position = read_entry
        schedules.append(schedule)
    return tuple(schedules), position


def locate_schedule_library(
    section: bytes, blocks_end: int, layout: TrainingLayout
) -> tuple[TrainingSchedule, ...]:
    """The saved schedules the section holds after its last team block, in stored order.

    Empty when nothing after the blocks has the shape of a group of saved schedules, which is
    what a save with no schedule of the manager's own looks like. Nothing raises here: the
    library is found by shape, so bytes that are not a group are simply not one.
    """
    prefix = layout.library_group_prefix
    schedules: list[TrainingSchedule] = []
    position = max(blocks_end, 0)
    while position < len(section):
        found = find_marker(section, prefix, position, len(section))
        if found < 0:
            break
        read_group = _library_group(section, found + len(prefix), layout)
        if read_group is None:
            position = found + 1
            continue
        group_schedules, group_end = read_group
        schedules.extend(group_schedules)
        position = group_end
    return tuple(schedules)


def build_training_tables(
    blocks: Sequence[RawTrainingBlock],
    library: tuple[TrainingSchedule, ...],
    club_index: ClubIndex,
    player_records: PlayerRecords,
    players: Table[Player],
    managed_club_uid: int,
    counts: TrainingWalkCounts,
) -> tuple[tuple[TeamTraining, ...], tuple[MentoringGroup, ...], TrainingStats]:
    """One row per block and one per mentoring group, with their club and player joins.

    A team the managed club fields at a club it controls maps to the managed club itself, with
    the slot that team holds in the managed club's own list, because that is the club whose
    training screen shows it. A member whose stored selector names no player record leaves that
    entry's uid and name empty and is counted.
    """
    club_for_team = club_index.team_to_club.get
    affiliate_club_for_team = club_index.affiliate_team_to_club.get
    club_by_uid = club_index.club_by_uid
    position_by_pindex = player_records.position_by_pindex
    player_uids = player_records.uids
    managed_club = club_by_uid.get(managed_club_uid)
    team_rows: list[TeamTraining] = []
    group_rows: list[MentoringGroup] = []
    member_count = 0
    resolved_count = 0
    at_club_count = 0
    for block in blocks:
        listed_club = affiliate_club_for_team(block.team_id) or club_for_team(block.team_id)
        club_uid, team_slot = listed_club if listed_club is not None else (None, None)
        club = None if club_uid is None else club_by_uid.get(club_uid)
        club_name = None if club is None else club.name
        team_rows.append(
            TeamTraining(block.team_id, club_uid, club_name, team_slot, block.weeks, library)
        )
        for group_number, label, selectors in block.groups:
            member_uids: list[int | None] = []
            member_names: list[str | None] = []
            for selector in selectors:
                member_count += 1
                record_position = position_by_pindex.get(selector - 1)
                if record_position is None:
                    member_uids.append(None)
                    member_names.append(None)
                    continue
                resolved_count += 1
                player_uid = player_uids[record_position]
                player = players.get_by_uid(player_uid)
                if player is not None and player.club_uid == managed_club_uid:
                    at_club_count += 1
                member_uids.append(player_uid)
                member_names.append(None if player is None else player.name)
            group_rows.append(
                MentoringGroup(
                    block.team_id,
                    club_uid,
                    club_name,
                    team_slot,
                    group_number,
                    label,
                    tuple(member_uids),
                    tuple(member_names),
                )
            )
    stats = TrainingStats(
        managed_club_exists=True,
        club_team_count=0 if managed_club is None else len(managed_club.teams),
        blocks=len(blocks),
        header_entries=counts.header_entries,
        weeks=counts.weeks,
        week_steps=counts.week_steps,
        seven_day_steps=counts.seven_day_steps,
        undated_weeks=counts.undated_weeks,
        library_entries=len(library),
        groups=len(group_rows),
        members=member_count,
        members_resolved=resolved_count,
        members_at_club=at_club_count,
    )
    return tuple(team_rows), tuple(group_rows), stats


def unmanaged_training_stats() -> TrainingStats:
    """The counts of a save whose manager runs no club, which holds no calendar at all."""
    return TrainingStats(
        managed_club_exists=False,
        club_team_count=0,
        blocks=0,
        header_entries=0,
        weeks=0,
        week_steps=0,
        seven_day_steps=0,
        undated_weeks=0,
        library_entries=0,
        groups=0,
        members=0,
        members_resolved=0,
        members_at_club=0,
    )
