"""Locate nullable match-cache declarations through owned, bounded field grammar.

Intervening property meanings remain unconfirmed. This walk neither scans for zero bytes
nor decodes match rows, and unknown or incomplete preceding fields never imply absence.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Literal

from fm26save._core._layouts import MatchCacheLayout
from fm26save._core._scan import decode_date

_U32 = struct.Struct("<I")
_NULL_DATE = b"\x01\x00\x6c\x07"
type CacheState = Literal["containing_null", "null", "empty", "nonempty", "unknown"]


@dataclass(frozen=True, slots=True)
class CacheDeclaration:
    state: CacheState
    offset: int | None = None


@dataclass(frozen=True, slots=True)
class CacheDeclarations:
    slots: int
    containing_null: int
    null: int
    empty: int
    nonempty: int
    unknown: int


class _UnknownCache(Exception):
    """The owned field grammar cannot establish a declaration."""


def _need(at: int, size: int, end: int) -> int:
    if at < 0 or size < 0 or at + size > end:
        raise _UnknownCache
    return at + size


def _date(data: bytes, at: int, end: int) -> bool:
    _need(at, 4, end)
    return data[at : at + 4] == _NULL_DATE or decode_date(data, at) is not None


def _nullable(
    data: bytes, at: int, end: int, marker: bytes, size: int, dates: tuple[int, ...] = ()
) -> int:
    _need(at, 1, end)
    if data[at] == 0:
        return at + 1
    stop = _need(at, size, end)
    if data[at : at + len(marker)] != marker or any(
        not _date(data, at + offset, stop) for offset in dates
    ):
        raise _UnknownCache
    return stop


class MatchCacheWalker:
    """A specific FM field walk with counts bounded by the current player's bytes."""

    def __init__(self, layout: MatchCacheLayout) -> None:
        self.layout = layout
        self.scalar_bytes = dict(layout.tagged_scalar_bytes)
        self.child_widths = dict(layout.dated_child_widths)

    def _prefix(self, data: bytes, ability: int, end: int) -> int:
        layout = self.layout
        at = ability + layout.header_offset
        _need(at, _U32.size, end)
        count = _U32.unpack_from(data, at)[0]
        at = _need(at + _U32.size, count, end)
        stop = _need(at, layout.header_suffix_bytes, end)
        marker_at = at + layout.header_marker_offset
        if data[marker_at : marker_at + len(layout.header_marker)] != layout.header_marker:
            raise _UnknownCache
        at = stop
        _need(at, 1, end)
        if data[at] == 0:
            at += 1
        else:
            _need(at, 3, end)
            if data[at : at + 2] != b"\x01\x02":
                raise _UnknownCache
            count = data[at + 2]
            at += 3
            _need(at, count * layout.fixed_row_bytes, end)
            for _ in range(count):
                stop = at + layout.fixed_row_bytes
                if data[at : at + len(layout.fixed_row_marker)] != layout.fixed_row_marker or any(
                    not _date(data, at + offset, stop) for offset in layout.fixed_row_dates
                ):
                    raise _UnknownCache
                at = stop
        _need(at, 1, end)
        if data[at] == 0:
            at += 1
        elif data[at : at + 2] == b"\x01\x00":
            at = _need(at, 2, end)
        elif data[at : at + 2] == b"\x01\x01":
            _need(at, 6, end)
            count = _U32.unpack_from(data, at + 2)[0]
            at += 6
            _need(at, count * 8, end)
            for _ in range(count):
                stop = _need(at, 8, end)
                if data[at] != 5 or not _date(data, at + 2, stop) or data[at + 6] != 1:
                    raise _UnknownCache
                kind = data[at + 7]
                at = stop
                if kind == 10:
                    stop = _need(at, layout.tagged_expression_bytes, end)
                    if (
                        data[at : at + len(layout.tagged_expression_prefix)]
                        != layout.tagged_expression_prefix
                    ):
                        raise _UnknownCache
                    at = stop
                elif kind == 11:
                    _need(at, _U32.size, end)
                    children = _U32.unpack_from(data, at)[0]
                    at += _U32.size
                    _need(at, children * layout.tagged_child_bytes, end)
                    for _ in range(children):
                        if data[at : at + 2] != b"\x01\x02":
                            raise _UnknownCache
                        at += layout.tagged_child_bytes
                elif kind in self.scalar_bytes:
                    at = _need(at, self.scalar_bytes[kind], end)
                else:
                    raise _UnknownCache
        else:
            raise _UnknownCache
        _need(at, _U32.size, end)
        count = _U32.unpack_from(data, at)[0]
        at = _need(at + _U32.size, count * 2, end)
        first, second, third = layout.nullable_prefix_bytes
        at = _nullable(data, at, end, b"\x01\x01", first)
        at = _nullable(data, at, end, b"\x01\x02", second, (5,))
        at = _nullable(data, at, end, b"\x01\x01", third, (2,))
        stop = _need(at, layout.raw_body_bytes, end)
        if data[at] != 2:
            raise _UnknownCache
        at = stop
        stop = _need(at, layout.reference_bytes, end)
        if data[at + 4] != 0 or any(
            not _date(data, at + offset, stop) for offset in layout.reference_dates
        ):
            raise _UnknownCache
        at = stop
        _need(at, _U32.size, end)
        count = _U32.unpack_from(data, at)[0]
        at += _U32.size
        stop = _need(at, count, end)
        # Decode solely to validate the string's declared encoding; never interpret it.
        data[at:stop].decode("utf-8")
        at = _need(stop, layout.raw_suffix_bytes, end)
        _need(at, 1, end)
        if data[at] == 0:
            return at + 1
        if data[at] == 1:
            return _need(at, layout.attribute_block_bytes, end)
        raise _UnknownCache

    def _predecessor(self, data: bytes, at: int, end: int) -> int | None:
        layout = self.layout
        _need(at, 1, end)
        if data[at] == 0:
            return None
        if data[at] != 1:
            raise _UnknownCache
        at += 1
        _need(at, 1, end)
        count = data[at]
        at += 1
        _need(at, count * layout.medical_row_bytes, end)
        for _ in range(count):
            _need(at, 4, end)
            optional = data[at + 3]
            if data[at] != 2 or optional not in (0, 1):
                raise _UnknownCache
            stop = _need(
                at, layout.medical_row_bytes + layout.medical_optional_bytes * optional, end
            )
            if not _date(data, at + 4 + layout.medical_optional_bytes * optional, stop):
                raise _UnknownCache
            if optional and (data[at + 4] != 1 or not _date(data, at + 5, stop)):
                raise _UnknownCache
            at = stop
        _need(at, 1, end)
        count = data[at]
        at += 1
        for _ in range(count):
            _need(
                at, max(layout.dated_child_marker_offset, layout.dated_child_type_offset) + 1, end
            )
            if data[at + layout.dated_child_marker_offset] != 5 or not _date(
                data, at + layout.dated_child_date_offset, end
            ):
                raise _UnknownCache
            width = self.child_widths.get(data[at + layout.dated_child_type_offset])
            if width is None:
                raise _UnknownCache
            at = _need(at, width, end)
            _need(at, 2, end)
            if data[at : at + 2] == b"\xff\x00":
                at += 2
            else:
                stop = _need(at, layout.dated_attachment_bytes, end)
                if (
                    data[at : at + 3] != b"\x03\x01\x01"
                    or not _date(data, at + 3, stop)
                    or data[at + 12] != 0
                    or data[at + 17] != 0
                ):
                    raise _UnknownCache
                at = stop
        first, second, third, fourth, fifth = layout.nullable_suffix_bytes
        start = at
        at = _nullable(data, at, end, b"\x01\x03", first, (39,))
        if data[start] and data[at - 1] != 0:
            raise _UnknownCache
        at = _nullable(data, at, end, b"\x01\x05", second)
        at = _nullable(data, at, end, b"\x01\x04", third, (26, 30))
        at = _nullable(data, at, end, b"\x01\x01", fourth, (10,))
        return _nullable(data, at, end, b"\x01\x01", fifth, (14,))

    def locate(self, data: bytes, ability: int, end: int) -> CacheDeclaration:
        """Return unknown on unsupported, malformed or cross-owner field grammar."""
        if not 0 <= ability < end <= len(data):
            return CacheDeclaration("unknown")
        try:
            at = self._predecessor(data, self._prefix(data, ability, end), end)
            if at is None:
                return CacheDeclaration("containing_null")
            _need(at, 1, end)
            if data[at] == 0:
                return CacheDeclaration("null", at)
            if data[at] == 1:
                _need(at, 2, end)
                return CacheDeclaration("empty" if data[at + 1] == 0 else "nonempty", at)
        except (_UnknownCache, UnicodeDecodeError, IndexError, struct.error):
            pass
        return CacheDeclaration("unknown")
