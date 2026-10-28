"""The three name pools in `game_db`: first names, surnames and common names.

A stored name id is an index into one pool. Locating the pools walks every entry once
and records where each one sits, without decoding any text; `PoolIndex.name_at` decodes
a single name when a reader asks for it.
"""

from __future__ import annotations

import struct
from array import array
from collections.abc import Iterator
from dataclasses import dataclass, field

from fm26save._core._errors import CorruptSaveError, ReaderCheckError
from fm26save._core._layouts import NamePoolLayout
from fm26save._core.readers._common import MISSING_REFERENCE, layout_mismatch, section_label

POOL_NAMES = ("first names", "surnames", "common names")
OFFSET_TYPECODE = "Q"
NAME_POOLS_CACHE_KEY = "name_pools"

_COUNT_WORD = struct.Struct("<I")
_ENTRY_HEADER = struct.Struct("<II")
_LENGTH_WORD_AFTER_ENTRY_START = 4


def _pool_overrun(file_name: str, pool_name: str) -> CorruptSaveError:
    return CorruptSaveError(
        f"{section_label(file_name)}: the {pool_name} pool runs past the end of the section"
    )


@dataclass(frozen=True, slots=True)
class PoolIndex:
    """Where each entry of one name pool sits in `game_db`.

    `entry_offsets[i]` is the offset of entry i's byte length word; its UTF-8 text follows.
    """

    entry_offsets: array[int] = field(repr=False)
    entry_count: int
    file_name: str = field(repr=False)
    pool_name: str

    def name_at(self, buffer: bytes, index: int) -> str | None:
        """The name stored at `index`, or None for the missing id, an out-of-range index or a blank.

        Raises:
            CorruptSaveError: The name is not valid UTF-8 or lies outside `buffer`.
        """
        if index == MISSING_REFERENCE or not 0 <= index < self.entry_count:
            return None
        length_word_at = self.entry_offsets[index]
        text_start = length_word_at + _COUNT_WORD.size
        if text_start > len(buffer):
            raise self._name_error(index, "lies outside the section")
        name_length: int = _COUNT_WORD.unpack_from(buffer, length_word_at)[0]
        if name_length == 0:
            return None
        text_end = text_start + name_length
        if text_end > len(buffer):
            raise self._name_error(index, "lies outside the section")
        try:
            return buffer[text_start:text_end].decode("utf-8")
        except UnicodeDecodeError as error:
            raise self._name_error(index, "is not valid UTF-8") from error

    def _name_error(self, index: int, problem: str) -> CorruptSaveError:
        return CorruptSaveError(
            f"{section_label(self.file_name)}: name {index} of the {self.pool_name} pool {problem}"
        )


@dataclass(frozen=True, slots=True)
class NamePools:
    """The three pools in their stored order, and the first byte after the last one."""

    first_names: PoolIndex
    surnames: PoolIndex
    common_names: PoolIndex
    end_offset: int


def locate_name_pools(game_db: bytes, layout: NamePoolLayout, file_name: str) -> NamePools:
    """Find the pools after their signature and index every entry, decoding no text.

    Raises:
        ReaderCheckError: No signature leads to valid pools, multiple valid pool groups
            exist, an entry id differs from its index, or a name exceeds the layout's cap.
        CorruptSaveError: A pool runs past the end of `game_db`.
    """
    found: NamePools | None = None
    first_error: CorruptSaveError | ReaderCheckError | None = None
    for signature_at in _signature_candidates(game_db, layout):
        try:
            pools = _read_pools(game_db, signature_at + len(layout.signature), layout, file_name)
        except (CorruptSaveError, ReaderCheckError) as error:
            if first_error is None:
                first_error = error
            continue
        if found is not None:
            raise layout_mismatch(
                file_name, "name pools not found (their signature is missing or not unique)"
            )
        found = pools
    if found is not None:
        return found
    if first_error is not None:
        raise first_error
    raise layout_mismatch(
        file_name, "name pools not found (their signature is missing or not unique)"
    )


def _signature_candidates(game_db: bytes, layout: NamePoolLayout) -> Iterator[int]:
    """Capacity words can grow together and unchecked bytes may vary; every candidate still
    needs three checked pools."""
    signature = layout.signature
    unchecked = layout.unchecked_signature_bytes
    if layout.max_signature_scale == 1 and not unchecked:
        start = 0
        while (at := game_db.find(signature, start)) >= 0:
            yield at
            start = at + 1
        return
    words = struct.unpack("<6I", signature)
    prefix = signature[: min((8, *unchecked))]
    start = 0
    while (at := game_db.find(prefix, start)) >= 0:
        start = at + 1
        if at + len(signature) > len(game_db):
            continue
        stored_bytes = bytearray(game_db[at : at + len(signature)])
        for byte_at in unchecked:
            stored_bytes[byte_at] = 0
        stored = struct.unpack("<6I", stored_bytes)
        scale, remainder = divmod(stored[3], words[3])
        if (
            remainder == 0
            and 1 <= scale <= layout.max_signature_scale
            and stored[:2] == words[:2]
            and stored[2:5] == tuple(value * scale for value in words[2:5])
            and stored[5] == words[5]
        ):
            yield at


def _read_pools(game_db: bytes, cursor: int, layout: NamePoolLayout, file_name: str) -> NamePools:
    pool_indexes: list[PoolIndex] = []
    for pool_name in POOL_NAMES:
        pool_index, cursor = _index_pool(game_db, cursor, layout, file_name, pool_name)
        pool_indexes.append(pool_index)
    first_names, surnames, common_names = pool_indexes
    return NamePools(
        first_names=first_names, surnames=surnames, common_names=common_names, end_offset=cursor
    )


def _index_pool(
    game_db: bytes,
    count_word_at: int,
    layout: NamePoolLayout,
    file_name: str,
    pool_name: str,
) -> tuple[PoolIndex, int]:
    """Walk one pool starting at its entry count; return its index and the offset after it."""
    buffer_length = len(game_db)
    position = count_word_at + _COUNT_WORD.size
    if position > buffer_length:
        raise _pool_overrun(file_name, pool_name)
    entry_count: int = _COUNT_WORD.unpack_from(game_db, count_word_at)[0]
    if entry_count * _ENTRY_HEADER.size > buffer_length - position:
        raise CorruptSaveError(
            f"{section_label(file_name)}: the {pool_name} pool claims {entry_count} entries, "
            "more than the rest of the section can hold"
        )
    entry_offsets = array(OFFSET_TYPECODE)
    record_offset = entry_offsets.append
    read_entry_header = _ENTRY_HEADER.unpack_from
    max_name_bytes = layout.max_name_bytes
    header_size = _ENTRY_HEADER.size
    last_header_start = buffer_length - header_size
    for entry_index in range(entry_count):
        if position > last_header_start:
            raise _pool_overrun(file_name, pool_name)
        entry_id, name_length = read_entry_header(game_db, position)
        if entry_id != entry_index or name_length > max_name_bytes:
            raise _entry_mismatch(file_name, pool_name, entry_index, entry_id, name_length, layout)
        record_offset(position + _LENGTH_WORD_AFTER_ENTRY_START)
        position += header_size + name_length
    if position > buffer_length:
        raise _pool_overrun(file_name, pool_name)
    pool_index = PoolIndex(
        entry_offsets=entry_offsets,
        entry_count=entry_count,
        file_name=file_name,
        pool_name=pool_name,
    )
    return pool_index, position


def _entry_mismatch(
    file_name: str,
    pool_name: str,
    entry_index: int,
    entry_id: int,
    name_length: int,
    layout: NamePoolLayout,
) -> ReaderCheckError:
    if entry_id != entry_index:
        detail = f"entry {entry_index} of the {pool_name} pool has id {entry_id}"
    else:
        detail = (
            f"entry {entry_index} of the {pool_name} pool is {name_length} bytes long, more than "
            f"the {layout.max_name_bytes} allowed"
        )
    return layout_mismatch(file_name, detail)
