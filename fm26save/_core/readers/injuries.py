"""Reading the injury-type names, and the injury history the save keeps against its people.

The names come out of a per-match file. No section of the save holds them: every per-match
directory entry carries one copy of the table, a few hundred bytes into its payload. The table
is found structurally and never by its text, because the names are in whatever language the
save was written in: a compiled seed pattern finds every place a record of the right shape
could start, each seed is walked as strictly as the layout allows, and the longest chain of
records is the table. Only as many entries are read as it takes to find one, so a save with
hundreds of them is never read whole.

The history comes out of a section of its own, walked whole: four arrays of fixed-stride rows,
three lists and an eight-byte tail, back to back with nothing between them. Nothing is searched
for and there is nothing to resynchronise on, so the walk itself is the structural check: a
count read one byte out of place claims either far more bytes than the section holds or too few
to reach the tail.
"""

from __future__ import annotations

import functools
import re
import struct
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from fm26save._core._container import DirectoryEntry
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import InjuryManagerLayout, InjuryTypeTableLayout, find_layout
from fm26save._core._reader_stats import InjuryStats, InjuryTypeStats
from fm26save._core._scan import decode_date, decode_time_slot
from fm26save._core.models.common import CodedValue
from fm26save._core.models.injuries import (
    InjuryCause,
    InjuryRecord,
    InjuryRecordKind,
    InjurySeverity,
    InjuryType,
)
from fm26save._core.models.players import Player
from fm26save._core.readers._common import (
    INJURY_MANAGER_SECTION,
    MATCH_FILE_REGION,
    MISSING_REFERENCE,
    build_gap_padded_struct,
    layout_mismatch,
)
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.player_scan import PlayerRecords
from fm26save._core.table import Table

# (id, name, flag, second id) of one record of the table.
type InjuryTypeRecord = tuple[int, str, int, int]

_SECOND_ID = struct.Struct("<I")
_UINT32 = struct.Struct("<I")
# The flag that sits between a record's text and its second id.
_FLAG_BYTES = 1
# What a log row's team field holds when it names no team. No save measured stores either, but
# every other reader that ships a stored id reads them this way.
_NO_TEAM = frozenset({0, MISSING_REFERENCE})
# How far behind the in-game date a typed row has to sit to be counted as part of the tail. A
# week was once taken for the horizon the game keeps these rows to, and a later save state held
# a full day's rows behind it, so the count is reported and nothing is judged by it.
_TYPED_TAIL_DAYS = 7


def find_injury_type_layout(build: str) -> InjuryTypeTableLayout:
    """Look up the table layout for a build. A per-match entry carries no schema number."""
    return find_layout(InjuryTypeTableLayout, MATCH_FILE_REGION, None, build).layout


@functools.lru_cache(maxsize=8)
def _seed_pattern(layout: InjuryTypeTableLayout) -> re.Pattern[bytes]:
    """Every place a record of this layout's shape could start.

    The pattern is the lead byte, any id, and a length inside the layout's range read as a u32,
    which is the most of a record that can be matched without walking it.
    """
    lowest_length, highest_length = layout.length_range
    if not 0 < lowest_length <= highest_length < 256:
        raise ValueError(
            f"the injury type length range {layout.length_range} must be inside 1 to 255"
        )
    id_bytes = layout.length_offset - layout.id_offset
    return re.compile(
        re.escape(bytes((layout.lead_byte,)))
        + b".{%d}" % id_bytes
        + b"[%s-%s]" % (re.escape(bytes((lowest_length,))), re.escape(bytes((highest_length,))))
        + b"\x00\x00\x00",
        re.DOTALL,
    )


@functools.lru_cache(maxsize=8)
def _record_head_struct(layout: InjuryTypeTableLayout) -> struct.Struct:
    """The lead byte, the id and the length, read from a record start.

    The walk reads the flag as the first byte after the text and the second id as the u32 after
    it, so a layout whose head offsets or whose trailer differ from that shape is rejected here
    rather than read from the wrong bytes.
    """
    if (layout.id_offset, layout.length_offset) != (1, 3):
        raise ValueError(
            "the injury type record head is a lead byte, a u16 id and a u32 length, so the id "
            "sits at offset 1 and the length at offset 3"
        )
    if layout.trailer_bytes != _FLAG_BYTES + _SECOND_ID.size:
        raise ValueError(
            "the injury type record trailer is a flag byte and a u32 second id, so it is "
            f"{_FLAG_BYTES + _SECOND_ID.size} bytes, not {layout.trailer_bytes}"
        )
    return struct.Struct("<BHI")


def _walk_chain(
    payload: bytes, start: int, layout: InjuryTypeTableLayout
) -> tuple[list[InjuryTypeRecord], int]:
    """Every record from `start` on, and the offset the walk stopped at.

    A record is accepted on the layout's own tests, and a chain runs only while each record's
    id is higher than the one before it, so a run of look-alike bytes ends the walk instead of
    being read as more of the table.
    """
    head_struct = _record_head_struct(layout)
    lowest_length, highest_length = layout.length_range
    lowest_text_byte, highest_text_byte = layout.text_byte_range
    records: list[InjuryTypeRecord] = []
    cursor = start
    previous_id = -1
    while cursor + layout.record_overhead_bytes <= len(payload):
        record_head: tuple[int, int, int] = head_struct.unpack_from(payload, cursor)
        lead_byte, type_id, name_length = record_head
        if lead_byte != layout.lead_byte or not lowest_length <= name_length <= highest_length:
            break
        text_end = cursor + layout.text_offset + name_length
        if text_end + layout.trailer_bytes > len(payload):
            break
        name_bytes = payload[cursor + layout.text_offset : text_end]
        if min(name_bytes) < lowest_text_byte or max(name_bytes) > highest_text_byte:
            break
        try:
            name = name_bytes.decode("utf-8")
        except UnicodeDecodeError:
            break
        if not all(
            character.isprintable() or unicodedata.category(character) == "Zs" for character in name
        ):
            break
        flag = payload[text_end]
        if flag not in layout.flag_values or type_id <= previous_id:
            break
        second_id: int = _SECOND_ID.unpack_from(payload, text_end + 1)[0]
        records.append((type_id, name, flag, second_id))
        previous_id = type_id
        cursor = text_end + layout.trailer_bytes
    return records, cursor


def locate_injury_type_table(
    payload: bytes, layout: InjuryTypeTableLayout
) -> tuple[InjuryTypeRecord, ...]:
    """The injury-type table inside one per-match payload, empty when it holds none.

    Every seed is walked, except seeds inside a chain already walked, and the longest chain
    wins; two chains of the same length settle on the earlier one. A chain shorter than the
    layout's minimum is no table.
    """
    seed_pattern = _seed_pattern(layout)
    longest_chain: list[InjuryTypeRecord] = []
    walked_to = 0
    search_from = 0
    while (seed := seed_pattern.search(payload, search_from)) is not None:
        seed_start = seed.start()
        search_from = seed_start + 1
        if seed_start < walked_to:
            continue
        records, chain_end = _walk_chain(payload, seed_start, layout)
        if records:
            walked_to = chain_end
        if len(records) > len(longest_chain):
            longest_chain = records
    if len(longest_chain) < layout.minimum_chain_entries:
        return ()
    return tuple(longest_chain)


def read_injury_types(
    entries: Sequence[DirectoryEntry],
    read_entry: Callable[[DirectoryEntry], bytes],
    layout: InjuryTypeTableLayout,
) -> tuple[tuple[InjuryType, ...], InjuryTypeStats]:
    """The named injury types of the first per-match entry that holds the table.

    Entries are read in directory order and only until one holds a table: at most
    `layout.maximum_entries_tried` of those that carry the per-match magic, and at most
    `layout.maximum_entries_opened` entries decompressed whatever they hold, so a save listing
    hundreds of them is never read whole even when not one of them is a per-match file. An
    entry without the magic is not a per-match file: it is counted, skipped, and does not count
    against the first limit. A save with no such entry, and one whose entries hold no table,
    both give a table of no rows.
    """
    entries_with_magic_tried = 0
    entries_without_magic = 0
    records: tuple[InjuryTypeRecord, ...] = ()
    for entry in entries:
        entries_opened = entries_with_magic_tried + entries_without_magic
        if (
            entries_with_magic_tried >= layout.maximum_entries_tried
            or entries_opened >= layout.maximum_entries_opened
        ):
            break
        payload = read_entry(entry)
        if not payload.startswith(layout.payload_prefix):
            entries_without_magic += 1
            continue
        entries_with_magic_tried += 1
        records = locate_injury_type_table(payload, layout)
        if records:
            break
    injury_types = tuple(
        InjuryType(type_id, name, FrozenMapping({"flag": flag, "second_id": second_id}))
        for type_id, name, flag, second_id in records
    )
    stats = InjuryTypeStats(
        match_entries=len(entries),
        entries_with_magic_tried=entries_with_magic_tried,
        entries_without_magic=entries_without_magic,
        table_entries=len(injury_types),
    )
    return injury_types, stats


@dataclass(frozen=True, slots=True)
class InjuryManagerWalk:
    """Where the rows of the `injury_manager` section are, and how much of each part it holds.

    `typed_offset` and `log_offset` are the first row of each of the two arrays whose rows
    fmsave ships; the window row counts and the list entry counts are all that is kept of the
    other five parts.
    """

    window_a_rows: int
    window_b_rows: int
    typed_offset: int
    typed_rows: int
    log_offset: int
    log_rows: int
    list_entries: tuple[int, ...]

    def __repr__(self) -> str:
        return f"<fmsave InjuryManagerWalk {self.log_rows} log, {self.typed_rows} typed>"


@dataclass(frozen=True, slots=True)
class _InjuryRowFields:
    """One array's fields as a single struct read from the row start, derived once.

    The date is in the struct only so the build-time overlap and bounds checks cover its four
    bytes; its value comes from `decode_date`, which masks the time-of-day bits these dates
    carry. `subject` is a log row's team id and a typed row's injury type, and `code` and
    `extra` the cause and severity of a log row and the two unnamed bytes of a typed row.
    """

    fields_struct: struct.Struct
    lead_index: int
    selector_index: int
    subject_index: int
    code_index: int
    extra_index: int


def _row_fields(
    layout: InjuryManagerLayout, stride: int, field_specs: Sequence[tuple[int, str, str]]
) -> _InjuryRowFields:
    """The struct for one array's rows, with every field held inside the stride.

    Raises:
        ValueError: A date starts where the lead byte sits, two fields overlap, or a field
            ends past the row's own last byte.
    """
    if layout.date_offset == 0:
        raise ValueError("the injury row lead byte sits at offset 0, so no date may start there")
    for offset, format_code, field_name in field_specs:
        if offset + struct.calcsize(format_code) > stride:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the {stride}-byte injury row"
            )
    fields_struct, _start_offset, index_by_name = build_gap_padded_struct(
        [(0, "B", "lead"), *field_specs], start_offset=0
    )
    return _InjuryRowFields(
        fields_struct=fields_struct,
        lead_index=index_by_name["lead"],
        selector_index=index_by_name["selector"],
        subject_index=index_by_name["subject"],
        code_index=index_by_name["code"],
        extra_index=index_by_name["extra"],
    )


@functools.lru_cache(maxsize=8)
def _log_row_fields(layout: InjuryManagerLayout) -> _InjuryRowFields:
    """The log array's row struct: the date, the person, the team and the two codes."""
    return _row_fields(
        layout,
        layout.array_strides[layout.log_array_index],
        [
            (layout.date_offset, "I", "date"),
            (layout.selector_offset, "I", "selector"),
            (layout.log_team_offset, "I", "subject"),
            (layout.log_cause_offset, "B", "code"),
            (layout.log_severity_offset, "B", "extra"),
        ],
    )


@functools.lru_cache(maxsize=8)
def _typed_row_fields(layout: InjuryManagerLayout) -> _InjuryRowFields:
    """The typed array's row struct: the date, the person, the type and two unnamed bytes."""
    return _row_fields(
        layout,
        layout.array_strides[layout.typed_array_index],
        [
            (layout.date_offset, "I", "date"),
            (layout.selector_offset, "I", "selector"),
            (layout.typed_type_offset, "H", "subject"),
            (layout.typed_r11_offset, "B", "code"),
            (layout.typed_r12_offset, "B", "extra"),
        ],
    )


def find_injury_manager_layout(schema: int | None, build: str) -> InjuryManagerLayout:
    """Look up the injury layout for an `injury_manager` schema, falling back to the build."""
    return find_layout(InjuryManagerLayout, INJURY_MANAGER_SECTION, schema, build).layout


def walk_injury_manager(
    section: bytes, layout: InjuryManagerLayout, file_name: str
) -> InjuryManagerWalk:
    """Consume the whole section: four arrays, three lists, then the tail and nothing else.

    Every count is judged against the bytes left before a single row is read from it, and the
    walk has to end on the section's last byte. That is the structural check in full, and it
    is what catches a wrong start offset or a wrong stride: there is no signature to search
    for here, so a walk that reads one count out of the middle of a row claims either far more
    bytes than the section holds or too few to reach the tail.

    Raises:
        ReaderCheckError: A count runs past the end of the section, the bytes where the tail
            belongs are not the tail, or the walk does not end on the section's last byte.
        ValueError: The layout does not name exactly two arrays besides its typed and log ones.
    """
    kept_indexes = (layout.typed_array_index, layout.log_array_index)
    row_counts: list[int] = []
    row_offsets: list[int] = []
    cursor = layout.arrays_offset
    section_bytes = len(section)
    for array_index, stride in enumerate(layout.array_strides):
        if cursor + _UINT32.size > section_bytes:
            raise layout_mismatch(
                file_name,
                f"the section holds {section_bytes} bytes and ends before array {array_index} "
                "says how many rows it holds",
                section_name=INJURY_MANAGER_SECTION,
            )
        (row_count,) = _UINT32.unpack_from(section, cursor)
        cursor += _UINT32.size
        if row_count > (section_bytes - cursor) // stride:
            raise layout_mismatch(
                file_name,
                f"array {array_index} claims {row_count} rows of {stride} bytes and only "
                f"{section_bytes - cursor} bytes are left",
                section_name=INJURY_MANAGER_SECTION,
            )
        row_offsets.append(cursor)
        row_counts.append(row_count)
        cursor += row_count * stride
    list_entries: list[int] = []
    for list_index, entry_bytes in enumerate(layout.list_entry_bytes):
        if cursor + _UINT32.size > section_bytes:
            raise layout_mismatch(
                file_name,
                f"the section ends before list {list_index} says how many entries it holds",
                section_name=INJURY_MANAGER_SECTION,
            )
        (entry_count,) = _UINT32.unpack_from(section, cursor)
        cursor += _UINT32.size
        if entry_count > (section_bytes - cursor) // entry_bytes:
            raise layout_mismatch(
                file_name,
                f"list {list_index} claims {entry_count} entries of {entry_bytes} bytes and "
                f"only {section_bytes - cursor} bytes are left",
                section_name=INJURY_MANAGER_SECTION,
            )
        list_entries.append(entry_count)
        cursor += entry_count * entry_bytes
    tail_end = cursor + len(layout.tail)
    if tail_end > section_bytes or section[cursor:tail_end] != layout.tail:
        raise layout_mismatch(
            file_name,
            f"the {len(layout.tail)} bytes where the section's tail belongs are not it",
            section_name=INJURY_MANAGER_SECTION,
        )
    if tail_end != section_bytes:
        raise layout_mismatch(
            file_name,
            f"{section_bytes - tail_end} bytes follow the section's tail",
            section_name=INJURY_MANAGER_SECTION,
        )
    window_counts = [
        row_count
        for array_index, row_count in enumerate(row_counts)
        if array_index not in kept_indexes
    ]
    if len(window_counts) != 2:
        raise ValueError(
            "the injury layout must name exactly two arrays besides its typed and log ones, "
            f"not {len(window_counts)}"
        )
    return InjuryManagerWalk(
        window_a_rows=window_counts[0],
        window_b_rows=window_counts[1],
        typed_offset=row_offsets[layout.typed_array_index],
        typed_rows=row_counts[layout.typed_array_index],
        log_offset=row_offsets[layout.log_array_index],
        log_rows=row_counts[layout.log_array_index],
        list_entries=tuple(list_entries),
    )


def build_injury_records(
    section: bytes,
    walk: InjuryManagerWalk,
    player_records: PlayerRecords,
    players: Table[Player],
    club_index: ClubIndex,
    injury_types: Table[InjuryType],
    clock: date,
    layout: InjuryManagerLayout,
) -> tuple[tuple[InjuryRecord, ...], InjuryStats]:
    """Every log row as a HISTORY record, then every typed row as a TYPED record.

    A typed row's date is the day the player is **expected back**, not the day he was hurt,
    which is why so many of these dates sit ahead of the in-game date. A typed row whose code
    the save's own name table has no entry for carries no name at all: fmsave ships no injury
    names of its own.

    A row's person is the stored selector less one, looked up among the player records: a
    person the save no longer keeps as a player leaves the uid and the name empty and is
    counted, because the game still shows that injury. A log row's team is looked up as
    stored, and a team another club controls names that controlling club, so a row against a
    reserve or affiliate side reads as the club that fields it. A team field holding zero or
    the missing-reference value names no team at all and leaves the team and club fields
    empty, as every other reader that ships a stored id does.

    Nothing is dropped and nothing is guessed. Every count the checks need comes out of this
    one pass, including the two joins that judge it: how many team ids a club lists at all,
    and how many of the rows from the last month name the team their player is registered
    with today.
    """
    log_fields = _log_row_fields(layout)
    typed_fields = _typed_row_fields(layout)
    log_stride = layout.array_strides[layout.log_array_index]
    typed_stride = layout.array_strides[layout.typed_array_index]
    position_by_pindex = player_records.position_by_pindex
    record_uids = player_records.uids
    # The table keeps its own uid index, so a second one here would hold a reference to every
    # player beside a table that already does.
    player_by_uid = players.get_by_uid
    club_by_team = club_index.team_to_club.get
    club_by_controlled_team = club_index.affiliate_team_to_club.get
    club_by_uid = club_index.club_by_uid.get
    name_by_type_id = {injury_type.id: injury_type.name for injury_type in injury_types}
    lead_byte = layout.lead_byte
    recent_from = clock - timedelta(days=layout.recent_log_days)
    clock_band = timedelta(days=layout.typed_clock_band_days)
    band_starts = clock - clock_band
    band_ends = clock + clock_band
    tail_starts = clock - timedelta(days=_TYPED_TAIL_DAYS)

    records: list[InjuryRecord] = []
    log_lead_ok = 0
    log_dates_ok = 0
    log_steps = 0
    log_ascending_steps = 0
    log_players_resolved = 0
    log_teams_resolved = 0
    recent_log_rows = 0
    recent_log_team_matches = 0
    previous_log_date: date | None = None
    unpack_log_row = log_fields.fields_struct.unpack_from
    for row_index in range(walk.log_rows):
        row_offset = walk.log_offset + row_index * log_stride
        field_values = unpack_log_row(section, row_offset)
        stored_lead: int = field_values[log_fields.lead_index]
        if stored_lead == lead_byte:
            log_lead_ok += 1
        date_offset = row_offset + layout.date_offset
        injury_date = decode_date(section, date_offset)
        if injury_date is not None:
            if injury_date <= clock:
                log_dates_ok += 1
            if previous_log_date is not None:
                log_steps += 1
                if injury_date >= previous_log_date:
                    log_ascending_steps += 1
            previous_log_date = injury_date
        selector: int = field_values[log_fields.selector_index]
        record_position = position_by_pindex.get(selector - 1)
        player_uid = None if record_position is None else record_uids[record_position]
        player = None if player_uid is None else player_by_uid(player_uid)
        if player_uid is not None:
            log_players_resolved += 1
        stored_team_id: int = field_values[log_fields.subject_index]
        team_id = None if stored_team_id in _NO_TEAM else stored_team_id
        team_club = (
            None if team_id is None else club_by_controlled_team(team_id) or club_by_team(team_id)
        )
        if team_club is None:
            club_uid: int | None = None
            team_slot: int | None = None
            club_name: str | None = None
        else:
            club_uid, team_slot = team_club
            log_teams_resolved += 1
            club = club_by_uid(club_uid)
            club_name = None if club is None else club.name
        if (
            injury_date is not None
            and injury_date >= recent_from
            and player is not None
            and player.team_id is not None
        ):
            recent_log_rows += 1
            if player.team_id == team_id:
                recent_log_team_matches += 1
        records.append(
            InjuryRecord(
                kind=InjuryRecordKind.HISTORY,
                player_uid=player_uid,
                player_name=None if player is None else player.name,
                date=injury_date,
                team_id=team_id,
                club_uid=club_uid,
                club_name=club_name,
                team_slot=team_slot,
                type_id=None,
                type_name=None,
                cause=CodedValue.from_raw(InjuryCause, field_values[log_fields.code_index]),
                severity=CodedValue.from_raw(InjurySeverity, field_values[log_fields.extra_index]),
                unknown=FrozenMapping(
                    {
                        "r0": stored_lead,
                        "hi7_date": decode_time_slot(section, date_offset),
                    }
                ),
            )
        )

    typed_lead_ok = 0
    typed_dated = 0
    typed_dated_near_clock = 0
    typed_dated_over_a_week_old = 0
    typed_players_resolved = 0
    typed_types_resolved = 0
    unpack_typed_row = typed_fields.fields_struct.unpack_from
    for row_index in range(walk.typed_rows):
        row_offset = walk.typed_offset + row_index * typed_stride
        field_values = unpack_typed_row(section, row_offset)
        stored_lead = field_values[typed_fields.lead_index]
        if stored_lead == lead_byte:
            typed_lead_ok += 1
        date_offset = row_offset + layout.date_offset
        typed_date = decode_date(section, date_offset)
        if typed_date is not None:
            typed_dated += 1
            if band_starts <= typed_date <= band_ends:
                typed_dated_near_clock += 1
            if typed_date < tail_starts:
                typed_dated_over_a_week_old += 1
        selector = field_values[typed_fields.selector_index]
        record_position = position_by_pindex.get(selector - 1)
        player_uid = None if record_position is None else record_uids[record_position]
        player = None if player_uid is None else player_by_uid(player_uid)
        if player_uid is not None:
            typed_players_resolved += 1
        type_id: int = field_values[typed_fields.subject_index]
        type_name = name_by_type_id.get(type_id)
        if type_name is not None:
            typed_types_resolved += 1
        records.append(
            InjuryRecord(
                kind=InjuryRecordKind.TYPED,
                player_uid=player_uid,
                player_name=None if player is None else player.name,
                date=typed_date,
                team_id=None,
                club_uid=None,
                club_name=None,
                team_slot=None,
                type_id=type_id,
                type_name=type_name,
                cause=None,
                severity=None,
                unknown=FrozenMapping(
                    {
                        "r0": stored_lead,
                        "r11": field_values[typed_fields.code_index],
                        "r12": field_values[typed_fields.extra_index],
                        "hi7_date": decode_time_slot(section, date_offset),
                    }
                ),
            )
        )

    stats = InjuryStats(
        section_bytes=len(section),
        window_a_rows=walk.window_a_rows,
        window_b_rows=walk.window_b_rows,
        list_entries=walk.list_entries,
        log_rows=walk.log_rows,
        log_lead_ok=log_lead_ok,
        log_dates_ok=log_dates_ok,
        log_steps=log_steps,
        log_ascending_steps=log_ascending_steps,
        log_players_resolved=log_players_resolved,
        log_teams_resolved=log_teams_resolved,
        recent_log_rows=recent_log_rows,
        recent_log_team_matches=recent_log_team_matches,
        typed_rows=walk.typed_rows,
        typed_lead_ok=typed_lead_ok,
        typed_dated=typed_dated,
        typed_dated_near_clock=typed_dated_near_clock,
        typed_dated_over_a_week_old=typed_dated_over_a_week_old,
        typed_players_resolved=typed_players_resolved,
        typed_types_resolved=typed_types_resolved,
        type_table_entries=len(injury_types),
    )
    return tuple(records), stats
