"""Walking the manager's team blocks in `tactics_man` and building the two tables from them.

Most of this section is a store of line-ups for other clubs, which this reader never walks.
What it does walk is the stored blocks of the managed club's teams, found by team id.
A team can have no stored block. Each block holds its team's selection, its copy of every
tactic the manager has, and its
set-piece routine groups.

Two rules keep the walk honest. A tactic record is bounded by the **next signature**, never by
the walk: the bytes after a record's last slot block are not decoded at all, so a record whose
slot walk breaks costs its own slots and nothing else, and the count in front of the records
says how many to look for. A routine is found by its terminator and decoded **backwards**, by
length: its name is never matched against text, because an empty slot stores a name of length
zero and one save's style code happens to be the terminator's own last four bytes.
"""

from __future__ import annotations

import functools
import re
import struct
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from fm26save._core._errors import ReaderCheckError
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import TacticsLayout, find_layout
from fm26save._core._reader_stats import TacticStats
from fm26save._core.models.common import CodedValue
from fm26save._core.models.players import Player
from fm26save._core.models.tactics import (
    Mentality,
    SetPieceRoutine,
    Tactic,
    TacticPosition,
    TacticSettingUnit,
    TacticSlot,
)
from fm26save._core.readers._common import MISSING_REFERENCE, TACTICS_SECTION, layout_mismatch
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.player_scan import PlayerRecords
from fm26save._core.table import Table

_UINT8 = struct.Struct("<B")
_UINT16 = struct.Struct("<H")
_UINT32 = struct.Struct("<I")
_UNIT_WORD_BITS = 32
_UNIT_WORD_MASK = (1 << _UNIT_WORD_BITS) - 1


@dataclass(frozen=True, slots=True)
class RawTactic:
    """One tactic record as the walk read it, before any club or team is joined to it.

    `mentality_raw` is the instruction byte the layout names as the mentality code, picked out
    here so the layout's own index is what decides which byte it is.

    `walk_complete` is False when the record's slot walk stopped early, in which case `slots`
    holds the slots decoded before it stopped. `oop_index_permutation` says whether the
    out-of-possession index bytes of the slots read are a permutation of 0 to one less than
    the number of slots a record holds.
    """

    name: str
    team_instructions: bytes
    mentality_raw: int
    style_name: str
    style_code: int
    slots: tuple[TacticSlot, ...]
    walk_complete: bool
    oop_index_permutation: bool


@dataclass(frozen=True, slots=True)
class RawTacticBlock:
    """One team block as the walk read it: its team, its tactics and its routine slots.

    `selectors` holds every player selector the block's selection part stores, which the table
    builder resolves for the reader's checks and never ships.
    """

    team_id: int
    tactics: tuple[RawTactic, ...]
    routine_names: tuple[str | None, ...]
    selectors: tuple[int, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class TacticWalkCounts:
    """What the walk over the team blocks counted, besides what the blocks themselves hold.

    `club_team_count` is how many teams the managed club fields, `blocks_found` how many of
    them the section stores exactly one block for, and `header_blocks` the number of blocks
    the section header claims. `stored_blocks` is how many blocks the section holds, found by
    structure rather than by team id, which includes the blocks of any national teams the
    manager also runs; it is 0 when the first one is not where the header ends.
    `stored_club_blocks` counts structurally located blocks naming one of the club teams.
    A club team can have no stored block. Duplicate blocks count separately here, so the
    team-id locator must still account for each stored block.
    `tactic_blocks` counts blocks whose stored count claims a tactic record, and
    `tactic_blocks_count_matching` those where every record the count claims was found. `preset_tactics` counts the records carrying the preset signature, which are
    decoded along with the other records in the team's declared list. `routine_blocks_complete`
    counts blocks whose default runs and counted routine groups were all read completely.
    """

    club_team_count: int
    header_blocks: int
    stored_blocks: int
    stored_club_blocks: int
    blocks_found: int
    tactic_blocks: int
    tactic_blocks_count_matching: int
    preset_tactics: int
    routine_blocks_complete: int


def find_tactics_layout(schema: int | None, build: str) -> TacticsLayout:
    """Look up the tactics layout for a `tactics_man` schema, falling back to the build."""
    return find_layout(TacticsLayout, TACTICS_SECTION, schema, build).layout


def _too_short(file_name: str, what: str) -> Exception:
    return layout_mismatch(file_name, f"the section ends inside {what}", TACTICS_SECTION)


def read_tactics_header(section: bytes, layout: TacticsLayout, file_name: str) -> tuple[int, int]:
    """The human manager's selector and the number of team blocks the header claims.

    Raises:
        ReaderCheckError: The section is too short to hold its header, or the header's constant
            byte is not where the layout says it is.
    """
    if layout.first_block_offset > len(section):
        raise layout_mismatch(
            file_name,
            f"the section holds {len(section)} bytes, too few for its "
            f"{layout.first_block_offset}-byte header",
            TACTICS_SECTION,
        )
    if section[layout.header_marker_offset] != layout.header_marker:
        raise layout_mismatch(
            file_name,
            "the header's constant byte is not where fmsave expects it",
            TACTICS_SECTION,
        )
    (selector,) = _UINT32.unpack_from(section, layout.selector_offset)
    (block_count,) = _UINT32.unpack_from(section, layout.block_count_offset)
    return selector, block_count


def _block_starts(
    section: bytes, club_team_ids: Sequence[int], layout: TacticsLayout
) -> dict[int, int]:
    """The start offset of each team's own block, for the teams stored exactly once.

    A team id the six locator bytes match nowhere, or in several places, gets no block: a
    second match means the offset the walk would start from is a guess.
    """
    starts: dict[int, int] = {}
    for team_id in club_team_ids:
        needle = _UINT32.pack(team_id) + layout.block_marker
        first = section.find(needle)
        if first < 0 or section.find(needle, first + 1) >= 0:
            continue
        starts[team_id] = first
    return starts


def _stored_block_starts(section: bytes, layout: TacticsLayout, file_name: str) -> list[int]:
    """The start of every team block the section stores, in order, found by structure.

    A block is a team id, the block marker and a whole selection part, so every marker hit is
    tried as the end of a team id and kept when the selection part after it parses. This finds
    blocks for teams the club index does not list, such as the manager's national teams.
    """
    starts: list[int] = []
    marker_at = section.find(layout.block_marker, layout.first_block_offset + _UINT32.size)
    while marker_at >= 0:
        block_start = marker_at - _UINT32.size
        try:
            _read_selection_part(section, block_start, len(section), layout, file_name)
        except ReaderCheckError:
            pass
        else:
            starts.append(block_start)
        marker_at = section.find(layout.block_marker, marker_at + 1)
    return starts


def _read_text(
    section: bytes, cursor: int, limit: int, layout: TacticsLayout, file_name: str, what: str
) -> tuple[str, int]:
    """One length-prefixed UTF-8 string and the offset just past it, within `limit`."""
    lowest_length, highest_length = layout.name_length_range
    if cursor + _UINT32.size > limit:
        raise _too_short(file_name, f"the length of {what}")
    (length,) = _UINT32.unpack_from(section, cursor)
    cursor += _UINT32.size
    if not lowest_length <= length <= highest_length:
        raise layout_mismatch(
            file_name,
            f"{what} claims {length} bytes, outside the {lowest_length} to {highest_length} "
            "fmsave expects",
            TACTICS_SECTION,
        )
    if cursor + length > limit:
        raise _too_short(file_name, what)
    try:
        text = section[cursor : cursor + length].decode("utf-8")
    except UnicodeDecodeError as decode_error:
        raise layout_mismatch(file_name, f"{what} is not valid UTF-8", TACTICS_SECTION) from (
            decode_error
        )
    return text, cursor + length


def _read_selector_list(
    section: bytes, cursor: int, limit: int, layout: TacticsLayout, file_name: str, what: str
) -> tuple[tuple[int, ...], int]:
    """One selector list and the offset just past it.

    Nothing caps the count but the bytes left in the section: one list of 99 selectors exists
    on the saves measured, so a fixed cap would have to be wider than any shape check it gives.
    """
    if cursor + _UINT32.size > limit:
        raise _too_short(file_name, f"the count of {what}")
    (count,) = _UINT32.unpack_from(section, cursor)
    cursor += _UINT32.size
    item_bytes = _UINT8.size + _UINT32.size
    if count > (limit - cursor) // item_bytes:
        raise layout_mismatch(
            file_name,
            f"{what} claims {count} entries and the section ends first",
            TACTICS_SECTION,
        )
    selectors: list[int] = []
    for _ in range(count):
        if section[cursor] != layout.list_item_lead_byte:
            raise layout_mismatch(
                file_name, f"an entry of {what} is not led as fmsave expects", TACTICS_SECTION
            )
        selectors.append(_UINT32.unpack_from(section, cursor + _UINT8.size)[0])
        cursor += item_bytes
    return tuple(selectors), cursor


def _expect_bytes(section: bytes, cursor: int, expected: bytes, file_name: str, what: str) -> int:
    if section[cursor : cursor + len(expected)] != expected:
        raise layout_mismatch(file_name, f"{what} is not where fmsave expects it", TACTICS_SECTION)
    return cursor + len(expected)


@dataclass(frozen=True, slots=True)
class _SelectionPart:
    """One block's selection part: its selectors, its stored value and its tactic count."""

    selectors: tuple[int, ...]
    tactic_count: int
    end: int


def _read_selection_part(
    section: bytes, block_start: int, block_end: int, layout: TacticsLayout, file_name: str
) -> _SelectionPart:
    """Walk a block's selection part, which is read for its selectors and its tactic count.

    Nothing of the selection itself ships: which players are picked, who takes which set piece
    and how the squad is ordered are out of scope, and the walk is here to reach the tactic
    count and to count how many selectors name a player.

    Raises:
        ReaderCheckError: A constant the block is built around is not where the layout says,
            a count runs past the end of the section, or the section ends inside the part.
    """
    cursor = _expect_bytes(
        section,
        block_start + _UINT32.size,
        layout.block_marker,
        file_name,
        "a team block's marker",
    )
    _label, cursor = _read_text(section, cursor, block_end, layout, file_name, "a selection label")
    selectors: list[int] = []
    slots_bytes = layout.selection_slot_count * _UINT32.size
    if cursor + slots_bytes > block_end:
        raise _too_short(file_name, "a block's selection slots")
    for slot in range(layout.selection_slot_count):
        selectors.append(_UINT32.unpack_from(section, cursor + slot * _UINT32.size)[0])
    cursor += slots_bytes
    cursor = _expect_bytes(
        section, cursor, layout.selection_end_marker, file_name, "a selection's end marker"
    )
    for list_name in ("the first selector list", "the second selector list"):
        one_list, cursor = _read_selector_list(
            section, cursor, block_end, layout, file_name, list_name
        )
        selectors.extend(one_list)
    if cursor + _UINT8.size + _UINT32.size > block_end:
        raise _too_short(file_name, "a block's single selector")
    if section[cursor] != layout.list_item_lead_byte:
        raise layout_mismatch(
            file_name, "a block's single selector is not led as fmsave expects", TACTICS_SECTION
        )
    selectors.append(_UINT32.unpack_from(section, cursor + _UINT8.size)[0])
    cursor += _UINT8.size + _UINT32.size
    # The observed marker variants introduce the same counted selector lists. Accept
    # only a known marker, then validate every list and the following order marker.
    for marker in layout.taker_markers:
        if section[cursor : cursor + len(marker)] == marker:
            cursor += len(marker)
            break
    else:
        raise layout_mismatch(
            file_name, "a block's set-piece marker is not where fmsave expects it", TACTICS_SECTION
        )
    for _ in range(layout.taker_list_count):
        one_list, cursor = _read_selector_list(
            section, cursor, block_end, layout, file_name, "a set-piece list"
        )
        selectors.extend(one_list)
    cursor = _expect_bytes(
        section, cursor, layout.order_marker, file_name, "a block's order marker"
    )
    for _ in range(layout.order_list_count):
        one_list, cursor = _read_selector_list(
            section, cursor, block_end, layout, file_name, "an order list"
        )
        selectors.extend(one_list)
    if cursor + _UINT8.size + _UINT32.size + _UINT16.size > block_end:
        raise _too_short(file_name, "a block's tactic count")
    if section[cursor] != layout.tactic_count_lead_byte:
        raise layout_mismatch(
            file_name,
            "the byte in front of a block's tactic count is not zero as fmsave expects",
            TACTICS_SECTION,
        )
    cursor += _UINT8.size
    (tactics_value,) = _UINT32.unpack_from(section, cursor)
    cursor += _UINT32.size
    (tactic_count,) = _UINT16.unpack_from(section, cursor)
    # The word in front of the count is the layout's no-tactics value on exactly the blocks
    # whose count is zero, on every block of every save measured, so it is read as the flag it
    # is: a block that carries it holds no record whatever the count says.
    if tactics_value == layout.no_tactics_value:
        tactic_count = 0
    return _SelectionPart(
        tuple(selector for selector in selectors if selector != MISSING_REFERENCE),
        tactic_count,
        cursor + _UINT16.size,
    )


def decode_setting_unit(unit: bytes, layout: TacticsLayout) -> TacticSettingUnit:
    """One setting unit's head byte and its two bit fields, the wider one as three words."""
    first_field_at = len(layout.unit_lead) + _UINT8.size
    second_field_at = first_field_at + layout.unit_first_field_bytes + _UINT8.size
    head_byte = unit[len(layout.unit_lead)]
    first_bits = int.from_bytes(
        unit[first_field_at : first_field_at + layout.unit_first_field_bytes], "little"
    )
    second_field = int.from_bytes(
        unit[second_field_at : second_field_at + layout.unit_second_field_bytes], "little"
    )
    return TacticSettingUnit(
        head_byte,
        first_bits,
        second_field & _UNIT_WORD_MASK,
        (second_field >> _UNIT_WORD_BITS) & _UNIT_WORD_MASK,
        (second_field >> (2 * _UNIT_WORD_BITS)) & _UNIT_WORD_MASK,
    )


def _mask_positions(mask: int, layout: TacticsLayout) -> tuple[CodedValue[TacticPosition], ...]:
    """The positions a slot's mask sets, in ascending bit number, flags left out."""
    return tuple(
        CodedValue.from_raw(TacticPosition, bit_number)
        for bit_number in range(layout.position_bit_count)
        if mask >> bit_number & 1
    )


@dataclass(frozen=True, slots=True)
class _SlotBlock:
    """One of the 22 slot blocks of a tactic record."""

    mask: int
    setting_count: int
    settings: tuple[TacticSettingUnit, ...]
    role_bits: int
    trail_bits: int
    position_index: int | None
    end: int


def _read_slot_block(
    section: bytes, cursor: int, record_end: int, layout: TacticsLayout, *, with_index_byte: bool
) -> _SlotBlock | None:
    """One slot block, or None when the bytes at `cursor` are not one.

    `record_end` is where this record's own bytes stop, which is the next signature in the team
    block or the block's own end: a block that would reach past it is not this record's, so the
    walk stops instead of decoding the next record's bytes as this one's slots.

    A slot block that does not decode is not an error: it ends the record's walk, which is
    counted, and the record after it starts at the next signature either way.
    """
    if section[cursor : cursor + len(layout.slot_tag)] != layout.slot_tag:
        return None
    cursor += len(layout.slot_tag)
    if cursor + _UINT32.size + len(layout.slot_constant) + _UINT32.size > record_end:
        return None
    (mask,) = _UINT32.unpack_from(section, cursor)
    cursor += _UINT32.size
    if section[cursor : cursor + len(layout.slot_constant)] != layout.slot_constant:
        return None
    cursor += len(layout.slot_constant)
    (setting_count,) = _UINT32.unpack_from(section, cursor)
    cursor += _UINT32.size
    lowest_count, highest_count = layout.unit_count_range
    if not lowest_count <= setting_count <= highest_count:
        return None
    units_end = cursor + layout.role_bits_bytes + setting_count * layout.unit_bytes
    block_end = units_end + layout.trail_bytes + (_UINT8.size if with_index_byte else 0)
    if block_end > record_end:
        return None
    role_bits = int.from_bytes(section[cursor : cursor + layout.role_bits_bytes], "little")
    cursor += layout.role_bits_bytes
    settings: list[TacticSettingUnit] = []
    for _ in range(setting_count):
        unit = section[cursor : cursor + layout.unit_bytes]
        if unit[: len(layout.unit_lead)] != layout.unit_lead:
            return None
        if unit[len(layout.unit_lead) + _UINT8.size + layout.unit_first_field_bytes] != (
            layout.unit_separator
        ):
            return None
        settings.append(decode_setting_unit(unit, layout))
        cursor += layout.unit_bytes
    trail_bits = int.from_bytes(section[cursor : cursor + layout.trail_bytes], "little")
    cursor += layout.trail_bytes
    position_index = None
    if with_index_byte:
        position_index = section[cursor]
        cursor += _UINT8.size
    return _SlotBlock(
        mask, setting_count, tuple(settings), role_bits, trail_bits, position_index, cursor
    )


def _slot_from_pair(
    number: int, in_possession: _SlotBlock, out_of_possession: _SlotBlock, layout: TacticsLayout
) -> TacticSlot:
    unknown: dict[str, int] = {
        "in_possession_role_bits": in_possession.role_bits,
        "in_possession_trail_bits": in_possession.trail_bits,
        "out_of_possession_role_bits": out_of_possession.role_bits,
        "out_of_possession_trail_bits": out_of_possession.trail_bits,
    }
    if out_of_possession.position_index is not None:
        unknown["out_of_possession_position_index"] = out_of_possession.position_index
    return TacticSlot(
        number,
        _mask_positions(in_possession.mask, layout),
        in_possession.mask,
        in_possession.setting_count,
        in_possession.settings,
        _mask_positions(out_of_possession.mask, layout),
        out_of_possession.mask,
        out_of_possession.setting_count,
        out_of_possession.settings,
        FrozenMapping(unknown),
    )


def _read_tactic_record(
    section: bytes, signature_at: int, record_end: int, layout: TacticsLayout, file_name: str
) -> RawTactic:
    """One stored tactic record, walked as far as its slot blocks allow.

    `record_end` is where the record's own bytes stop: the next signature inside the team
    block, or the block's end when it is the last record. Nothing here reads past it, so a
    record whose walk breaks cannot take its slots from the record that follows it.

    Raises:
        ReaderCheckError: The record's name or style label does not decode, or its fixed part
            runs past the end of the record. The slot blocks are different: a slot that does
            not decode ends the walk and is reported, because the record after this one starts
            at the next signature rather than where this walk stopped.
    """
    cursor = signature_at + len(layout.user_signature)
    name, cursor = _read_text(section, cursor, record_end, layout, file_name, "a tactic name")
    cursor += layout.name_zero_bytes
    if cursor + layout.team_instruction_bytes > record_end:
        raise _too_short(file_name, "a tactic's team instructions")
    team_instructions = section[cursor : cursor + layout.team_instruction_bytes]
    cursor += layout.team_instruction_bytes
    style_name, cursor = _read_text(
        section, cursor, record_end, layout, file_name, "a tactic style label"
    )
    if cursor + layout.style_code_bytes > record_end:
        raise _too_short(file_name, "a tactic's style code")
    style_code = int.from_bytes(section[cursor : cursor + layout.style_code_bytes], "little")
    cursor += layout.style_code_bytes
    slots: list[TacticSlot] = []
    index_bytes: list[int] = []
    walk_complete = True
    for number in range(layout.slot_count):
        in_possession = _read_slot_block(section, cursor, record_end, layout, with_index_byte=False)
        if in_possession is None:
            walk_complete = False
            break
        out_of_possession = _read_slot_block(
            section, in_possession.end, record_end, layout, with_index_byte=True
        )
        if out_of_possession is None:
            walk_complete = False
            break
        slots.append(_slot_from_pair(number, in_possession, out_of_possession, layout))
        if out_of_possession.position_index is not None:
            index_bytes.append(out_of_possession.position_index)
        cursor = out_of_possession.end
    return RawTactic(
        name,
        bytes(team_instructions),
        team_instructions[layout.mentality_index],
        style_name,
        style_code,
        tuple(slots),
        walk_complete,
        sorted(index_bytes) == list(range(layout.slot_count)),
    )


def _read_routine_name(section: bytes, terminator_at: int, layout: TacticsLayout) -> str | None:
    """The name a routine terminator ends, decoded backwards by its stored length.

    The shortest length whose stored word sits exactly that many bytes in front of the
    terminator wins. A slot with no routine stores a length of zero, so an empty name is a
    routine and not a failure; None means these bytes end no routine at all.
    """
    lowest_length, highest_length = layout.routine_name_length_range
    for length in range(lowest_length, highest_length + 1):
        length_at = terminator_at - _UINT32.size - length
        if length_at < 0:
            return None
        (stored_length,) = _UINT32.unpack_from(section, length_at)
        if stored_length != length:
            continue
        candidate = section[length_at + _UINT32.size : length_at + _UINT32.size + length]
        try:
            text = candidate.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if any(character < " " for character in text):
            continue
        return text
    return None


@functools.cache
def _routine_tail_pattern(layout: TacticsLayout) -> re.Pattern[bytes]:
    """A routine's tail flag and four-character code, whichever flag and code it stores.

    The flag is not a constant: user routines store other values in it than default ones do.
    """

    def byte_class(low: int, high: int) -> bytes:
        return b"[" + re.escape(bytes((low,))) + b"-" + re.escape(bytes((high,))) + b"]"

    return re.compile(
        byte_class(*layout.routine_tail_flag_range)
        + byte_class(*layout.routine_code_byte_range)
        + b"{"
        + str(layout.routine_code_bytes).encode("ascii")
        + b"}"
    )


def _read_routine_groups(
    section: bytes, area: int, block_end: int, layout: TacticsLayout
) -> tuple[tuple[str | None, ...], bool]:
    """Read default routines and the stored counts of user-routine groups.

    A complete walk consumes every group, including its trailer byte. Terminators outside
    those groups cannot add routines or make a truncated group pass its check.
    """
    cursor = area + layout.routine_area_header_bytes
    next_record, _is_user = _next_signature(section, cursor, block_end, layout)
    if next_record is not None:
        block_end = next_record
    names: list[str | None] = []

    def read_one() -> bool:
        nonlocal cursor
        stop = min(block_end, cursor + layout.routine_record_max_bytes)
        for match in _routine_tail_pattern(layout).finditer(section, cursor, stop):
            terminator = match.start()
            name = _read_routine_name(section, terminator, layout)
            if name is None or terminator - len(name.encode("utf-8")) - 4 < cursor:
                continue
            end = match.end() + 1
            if end > block_end:
                return False
            names.append(name or None)
            cursor = end
            return True
        return False

    for group_size in layout.routine_group_sizes:
        for _ in range(group_size):
            if not read_one():
                return tuple(names), False
        for _ in range(group_size):
            if cursor + _UINT32.size > block_end:
                return tuple(names), False
            count = _UINT32.unpack_from(section, cursor)[0]
            cursor += _UINT32.size
            if (
                not layout.routine_group_count_range[0]
                <= count
                <= layout.routine_group_count_range[1]
            ):
                return tuple(names), False
            for _ in range(count):
                if not read_one():
                    return tuple(names), False
    return tuple(names), True


def _read_routines(
    section: bytes, search_from: int, block_end: int, layout: TacticsLayout
) -> tuple[tuple[str | None, ...], bool, int]:
    """Locate a complete counted area; a marker alone can occur in tactic setting bits.

    When no candidate completes, retain the first partial walk for its failed check.
    Its position still bounds tactics, so trailing library records cannot fill a missing
    record claimed by a team block.
    """
    first: tuple[tuple[str | None, ...], bool, int] | None = None
    area = section.find(layout.routine_area_marker, search_from, block_end)
    while area >= 0:
        names, complete = _read_routine_groups(section, area, block_end, layout)
        result = names, complete, area
        if complete:
            return result
        if first is None:
            first = result
        area = section.find(layout.routine_area_marker, area + 1, block_end)
    return ((), False, block_end) if first is None else first


def _next_signature(
    section: bytes, search_from: int, block_end: int, layout: TacticsLayout
) -> tuple[int | None, bool]:
    """(offset, whether it is a user record) of the next tactic signature, or (None, False).

    The supported signatures differ in their last byte alone, so all are searched for and the
    earlier one wins. This is what bounds a record: its own bytes end where the next
    signature begins.
    """
    found = (
        (section.find(signature, search_from, block_end), is_user)
        for signature, is_user in (
            (layout.user_signature, True),
            (layout.alternate_signature, True),
            (layout.preset_signature, False),
        )
    )
    return min((hit for hit in found if hit[0] >= 0), default=(None, False))


def walk_tactic_blocks(
    section: bytes,
    club_team_ids: Sequence[int],
    layout: TacticsLayout,
    file_name: str,
) -> tuple[tuple[RawTacticBlock, ...], TacticWalkCounts]:
    """Every team block of the managed club, in ascending team id, and what the walk counted.

    Each block is read as far as the structures this reader ships: its selectors, the tactic
    records its own count claims, and its set-piece routine slots. Records are located by
    signature and bounded by the next signature, so a record whose slot walk breaks does not
    move the next one.

    Raises:
        ReaderCheckError: The section is too short to hold its header, a constant a block is
            built around is not where the layout says it is, a count inside a block runs past
            the end of the section, or a name does not decode.
    """
    _selector, header_blocks = read_tactics_header(section, layout, file_name)
    starts = _block_starts(section, club_team_ids, layout)
    ordered_starts = sorted(starts.items(), key=lambda pair: pair[1])
    stored_starts = _stored_block_starts(section, layout, file_name)
    blocks: list[RawTacticBlock] = []
    routine_blocks_complete = 0
    tactic_blocks = 0
    tactic_blocks_count_matching = 0
    preset_tactics = 0
    for team_id, block_start in ordered_starts:
        # A block ends where the next stored block begins, whichever team that block is for:
        # the manager's national teams have blocks too, and the club index lists none of them.
        block_end = next((start for start in stored_starts if start > block_start), len(section))
        selection = _read_selection_part(section, block_start, block_end, layout, file_name)
        routine_names, routines_complete, records_end = _read_routines(
            section, selection.end, block_end, layout
        )
        tactics: list[RawTactic] = []
        records_found = 0
        search_from = selection.end
        for _ in range(selection.tactic_count):
            signature_at, is_user_record = _next_signature(
                section, search_from, records_end, layout
            )
            if signature_at is None:
                break
            records_found += 1
            search_from = signature_at + len(layout.user_signature)
            if not is_user_record:
                preset_tactics += 1
            next_signature_at, _next_is_user = _next_signature(
                section, search_from, records_end, layout
            )
            tactics.append(
                _read_tactic_record(
                    section,
                    signature_at,
                    records_end if next_signature_at is None else next_signature_at,
                    layout,
                    file_name,
                )
            )
        if selection.tactic_count:
            tactic_blocks += 1
            if records_found == selection.tactic_count:
                tactic_blocks_count_matching += 1
        # Routine groups have their own counts and boundary; an incomplete tactic walk must
        # not move their start past the area into trailing preset records.
        if routines_complete:
            routine_blocks_complete += 1
        blocks.append(RawTacticBlock(team_id, tuple(tactics), routine_names, selection.selectors))
    stored_block_count = (
        len(stored_starts) if stored_starts[:1] == [layout.first_block_offset] else 0
    )
    club_team_id_set = frozenset(club_team_ids)
    stored_club_blocks = (
        sum(_UINT32.unpack_from(section, start)[0] in club_team_id_set for start in stored_starts)
        if stored_block_count
        else 0
    )
    counts = TacticWalkCounts(
        len(club_team_ids),
        header_blocks,
        # Counted only when the first block sits where the header ends, so a scan that has
        # drifted off the real blocks cannot agree with the header by accident.
        stored_block_count,
        stored_club_blocks,
        len(blocks),
        tactic_blocks,
        tactic_blocks_count_matching,
        preset_tactics,
        routine_blocks_complete,
    )
    return tuple(blocks), counts


def _team_fields(team_id: int, club_index: ClubIndex) -> tuple[int | None, str | None, int | None]:
    """(club uid, club name, team slot) of a team, empty where no club lists it.

    A team another club fields for the club that controls it belongs to the controlling club,
    the same rule players follow, so the affiliate map is tried before the club's own teams.
    """
    found = club_index.affiliate_team_to_club.get(team_id) or club_index.team_to_club.get(team_id)
    if found is None:
        return None, None, None
    club_uid, team_slot = found
    club = club_index.club_by_uid.get(club_uid)
    return club_uid, None if club is None else club.name, team_slot


def _tactic_unknown(raw_tactic: RawTactic) -> Mapping[str, int]:
    unknown = {
        f"team_instruction_{position:02d}": value
        for position, value in enumerate(raw_tactic.team_instructions)
    }
    unknown["style_code"] = raw_tactic.style_code
    return FrozenMapping(unknown)


def _club_uid_by_player_uid(players: Iterable[Player]) -> dict[int, int | None]:
    return {player.uid: player.club_uid for player in players}


def build_tactic_tables(
    blocks: Sequence[RawTacticBlock],
    club_index: ClubIndex,
    player_records: PlayerRecords,
    players: Table[Player],
    managed_club_uid: int,
    header_selector: int,
    human_selector: int | None,
    counts: TacticWalkCounts,
) -> tuple[tuple[Tactic, ...], tuple[SetPieceRoutine, ...], TacticStats]:
    """Both tables and the counts the checks judge, from the blocks the walk read.

    A block's tactics keep their stored order and `index` counts all records of that block
    alone. Library records following its routine area are outside that list. Every
    routine slot of every block becomes a row, named or not.
    """
    club_uid_by_player_uid = _club_uid_by_player_uid(players)
    tactics: list[Tactic] = []
    routines: list[SetPieceRoutine] = []
    selectors = 0
    selectors_resolved = 0
    selectors_at_club = 0
    slot_walks_complete = 0
    index_permutations = 0
    named_routines = 0
    for raw_block in blocks:
        club_uid, club_name, team_slot = _team_fields(raw_block.team_id, club_index)
        for index, raw_tactic in enumerate(raw_block.tactics):
            if raw_tactic.walk_complete:
                slot_walks_complete += 1
            if raw_tactic.oop_index_permutation:
                index_permutations += 1
            tactics.append(
                Tactic(
                    club_uid,
                    club_name,
                    raw_block.team_id,
                    team_slot,
                    index,
                    raw_tactic.name,
                    raw_tactic.style_name,
                    CodedValue.from_raw(Mentality, raw_tactic.mentality_raw),
                    raw_tactic.slots,
                    _tactic_unknown(raw_tactic),
                )
            )
        for slot, name in enumerate(raw_block.routine_names):
            if name is not None:
                named_routines += 1
            routines.append(
                SetPieceRoutine(club_uid, club_name, raw_block.team_id, team_slot, slot, name)
            )
        for selector in raw_block.selectors:
            selectors += 1
            position = player_records.position_by_pindex.get(selector - 1)
            if position is None:
                continue
            selectors_resolved += 1
            if club_uid_by_player_uid.get(player_records.uids[position]) == managed_club_uid:
                selectors_at_club += 1
    stats = TacticStats(
        managed_club_exists=True,
        club_team_count=counts.club_team_count,
        header_blocks=counts.header_blocks,
        stored_blocks=counts.stored_blocks,
        stored_club_blocks=counts.stored_club_blocks,
        blocks_found=counts.blocks_found,
        selector_matches=human_selector is not None and header_selector == human_selector,
        selection_selectors=selectors,
        selection_selectors_resolved=selectors_resolved,
        selection_selectors_at_club=selectors_at_club,
        tactic_blocks=counts.tactic_blocks,
        tactic_blocks_count_matching=counts.tactic_blocks_count_matching,
        stored_tactics=len(tactics),
        preset_tactics=counts.preset_tactics,
        slot_walks_complete=slot_walks_complete,
        oop_index_permutations=index_permutations,
        routine_blocks=len(blocks),
        routine_blocks_complete=counts.routine_blocks_complete,
        routines=len(routines),
        named_routines=named_routines,
    )
    return tuple(tactics), tuple(routines), stats
