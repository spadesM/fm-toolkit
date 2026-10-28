"""Bounds-checked primitive reads, dates and bounded marker searches.

These are the only low-level loops over decompressed save bytes. Every read checks
its bounds first and reports problems as CorruptSaveError, so malformed input never
surfaces as struct.error or IndexError.
"""

from __future__ import annotations

import calendar
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta

from fm26save._core._errors import CorruptSaveError
from fm26save._core._layouts import TaggedStreamLayout

type Buffer = bytes | bytearray | memoryview
type SearchableBuffer = bytes | bytearray

_U16 = struct.Struct("<H")
_U32 = struct.Struct("<I")
_U64 = struct.Struct("<Q")

DAY_OF_YEAR_MASK = 0x1FF
TIME_SLOT_SHIFT = 9
EARLIEST_GAME_YEAR = 1901
LATEST_GAME_YEAR = 2200

# A stored tag is four printable ASCII bytes; anything else is not a record.
LOWEST_TAG_BYTE = 0x20
HIGHEST_TAG_BYTE = 0x7E


def _check_bounds(buffer: Buffer, offset: int, size: int) -> None:
    if offset < 0 or offset + size > len(buffer):
        raise CorruptSaveError(
            f"read of {size} bytes at offset {offset} is outside a {len(buffer)}-byte buffer"
        )


def _unpack(layout: struct.Struct, buffer: Buffer, offset: int) -> int:
    _check_bounds(buffer, offset, layout.size)
    value: int = layout.unpack_from(buffer, offset)[0]
    return value


def read_u16(buffer: Buffer, offset: int) -> int:
    return _unpack(_U16, buffer, offset)


def read_u32(buffer: Buffer, offset: int) -> int:
    return _unpack(_U32, buffer, offset)


def read_u64(buffer: Buffer, offset: int) -> int:
    return _unpack(_U64, buffer, offset)


def read_length_prefixed_string(buffer: Buffer, offset: int, max_length: int) -> tuple[str, int]:
    """Read a u32 length followed by that many UTF-8 bytes; return (text, offset after it)."""
    length = read_u32(buffer, offset)
    if length > max_length:
        raise CorruptSaveError(
            f"string at offset {offset} claims {length} bytes, more than the {max_length} allowed"
        )
    text_start = offset + 4
    _check_bounds(buffer, text_start, length)
    try:
        text = bytes(buffer[text_start : text_start + length]).decode("utf-8")
    except UnicodeDecodeError as error:
        raise CorruptSaveError(f"string at offset {offset} is not valid UTF-8") from error
    return text, text_start + length


def decode_date(buffer: Buffer, offset: int) -> date | None:
    """Decode a 4-byte game date, or None for the null date and malformed values."""
    packed = read_u16(buffer, offset)
    year = read_u16(buffer, offset + 2)
    day_of_year = packed & DAY_OF_YEAR_MASK
    if not EARLIEST_GAME_YEAR <= year <= LATEST_GAME_YEAR:
        return None
    days_in_year = 366 if calendar.isleap(year) else 365
    if not 1 <= day_of_year <= days_in_year:
        return None
    return date(year, 1, 1) + timedelta(days=day_of_year - 1)


def decode_time_slot(buffer: Buffer, offset: int) -> int:
    """The intra-day slot stored in the high bits of a game date."""
    return read_u16(buffer, offset) >> TIME_SLOT_SHIFT


def _check_search(buffer: SearchableBuffer, marker: bytes, start: int, end: int) -> None:
    if not marker:
        raise ValueError("marker must not be empty")
    if start < 0 or end > len(buffer) or start > end:
        raise CorruptSaveError(
            f"search range {start}..{end} is outside a {len(buffer)}-byte buffer"
        )


def find_marker(buffer: SearchableBuffer, marker: bytes, start: int, end: int) -> int:
    """Index of the first marker lying wholly inside [start, end), or -1."""
    _check_search(buffer, marker, start, end)
    return buffer.find(marker, start, end)


@dataclass(frozen=True, slots=True)
class TaggedValue:
    """One record of the game's tagged stream.

    Attributes:
        tag: The four stored tag bytes reversed and decoded as ASCII, so `csed` reads `desc`.
        kind: The type byte exactly as stored.
        value: The decoded value: an int for the integer and list types (a list type's value
            is its count), the text for the string type, and None for the nil type.
        offset: Where the record starts.
        end: One past the record's last byte, so a caller can resume from here.
    """

    tag: str
    kind: int
    value: int | str | None
    offset: int
    end: int


def iter_tagged_values(
    buffer: Buffer, start: int, end: int, layout: TaggedStreamLayout
) -> Iterator[TaggedValue]:
    """Walk the tagged stream from `start`, stopping at `end`, at an unknown type byte, or
    at a value that would run past `end`. Every read is bounds-checked.

    The walk is strict: it never steps over a byte it cannot read, so it stops at the first
    thing that is not a record rather than hunting for the next one. A caller that wants the
    records after a gap looks for its own anchor and walks again from there. Nothing here
    raises: a malformed stream simply ends the walk, and the caller decides what that means.
    """
    tag_bytes = layout.tag_bytes
    header_bytes = tag_bytes + 2
    separator_value = layout.separator_value
    u8_types = layout.u8_types
    u16_types = layout.u16_types
    u32_types = layout.u32_types
    string_type = layout.string_type
    list_type = layout.list_type
    nil_type = layout.nil_type
    max_string_bytes = layout.max_string_bytes
    limit = min(end, len(buffer))
    position = max(start, 0)
    while position + header_bytes <= limit:
        stored_tag = bytes(buffer[position : position + tag_bytes])
        if any(byte < LOWEST_TAG_BYTE or byte > HIGHEST_TAG_BYTE for byte in stored_tag):
            return
        if buffer[position + tag_bytes] != separator_value:
            return
        kind = buffer[position + tag_bytes + 1]
        value_start = position + header_bytes
        value: int | str | None
        if kind in u8_types:
            if value_start + 1 > limit:
                return
            value = buffer[value_start]
            value_end = value_start + 1
        elif kind in u16_types:
            if value_start + 2 > limit:
                return
            value = _U16.unpack_from(buffer, value_start)[0]
            value_end = value_start + 2
        elif kind in u32_types or kind == list_type:
            if value_start + 4 > limit:
                return
            value = _U32.unpack_from(buffer, value_start)[0]
            value_end = value_start + 4
        elif kind == string_type:
            if value_start + 4 > limit:
                return
            text_bytes: int = _U32.unpack_from(buffer, value_start)[0]
            text_start = value_start + 4
            if text_bytes > max_string_bytes or text_start + text_bytes > limit:
                return
            try:
                value = bytes(buffer[text_start : text_start + text_bytes]).decode("utf-8")
            except UnicodeDecodeError:
                return
            value_end = text_start + text_bytes
        elif kind == nil_type:
            value = None
            value_end = value_start
        else:
            return
        yield TaggedValue(stored_tag[::-1].decode("ascii"), kind, value, position, value_end)
        position = value_end
