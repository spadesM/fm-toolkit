"""Decoding one player's person block: names, birth date, nations, relations, traits and
personality.

A person block sits somewhere in the player record's window, found by searching for a
maximal in-range personality run's start (a `\\x00` byte immediately followed by
`personality_count` in-range bytes) and validating backwards from it. The search itself
never holds a save-wide buffer or slices the whole window: it walks `game_db` in small,
overlapping chunks, translating and discarding each one. `readers/players.py` calls
`PersonBlockDecoder.decode` once per player record and merges the result into `Player`.
`decode` returns a plain positional tuple, not a dataclass, so a successful decode
allocates only the `Personality` it builds and the tuples it returns.
"""

from __future__ import annotations

import functools
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import cast

from fm26save._core._errors import CorruptSaveError
from fm26save._core._layouts import PersonBlockLayout
from fm26save._core._scan import DAY_OF_YEAR_MASK, EARLIEST_GAME_YEAR, TIME_SLOT_SHIFT, decode_date
from fm26save._core.models.common import CodedValue
from fm26save._core.models.players import Personality, Trait
from fm26save._core.readers._common import MISSING_REFERENCE, build_gap_padded_struct, section_label
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.names import NamePools, PoolIndex

# One player's decoded person block, in `Player`'s person-field order:
# (name, first_name, last_name, common_name, full_name, legal_name, birth_date, age,
#  nation_id, second_nation_ids, home_grown_nation_ids, home_grown_club_uids,
#  home_grown_club_names, personality, trait_bits, traits)
type PersonTuple = tuple[
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    date | None,
    int | None,
    int,
    tuple[int, ...],
    tuple[int, ...],
    tuple[int | None, ...],
    tuple[str | None, ...],
    Personality,
    int,
    tuple[CodedValue[Trait], ...],
]

_BIRTH_WORD_STRUCT = struct.Struct("<I")  # day-of-year/slot (low 16 bits), year (high 16 bits)
_UINT32_STRUCT = struct.Struct("<I")
_UINT16_STRUCT = struct.Struct("<H")
# q-8 (trait bits), then the first-name, surname and common-name ids, each followed by its
# required zero byte: q+0/q+4, q+5/q+9, q+10/q+14.
_NAME_BLOCK_STRUCT = struct.Struct("<QIBIBIB")
# A relation entry unpacks as the referenced value (a u32), then kind and role read together as
# one little-endian u16 (kind is the low byte, role the high byte), then the qualifier byte and
# the sentinel byte, which only the person checks read. Every position comes from the layout.
_RELATION_FIELD_ORDER = ("referenced", "kind_role", "qualifier", "sentinel")
_RELATION_VALUES_PER_ENTRY = len(_RELATION_FIELD_ORDER)
_RELATION_SENTINEL_INDEX = _RELATION_FIELD_ORDER.index("sentinel")
_TRAIT_BIT_COUNT = 64
_NAME_CACHE_MISS = object()

# The chunked search: a 256-byte translate table maps 0x00 to _ZERO_MARKER, an in-range
# personality byte to _IN_RANGE_MARKER, and everything else to 0 (neither marker), so the
# needle "_ZERO_MARKER then personality_count _IN_RANGE_MARKER bytes" can be found with
# bytes.find instead of a regex. Chunks overlap by needle_length - 1 bytes so a run whose
# leading zero byte falls in one chunk but whose in-range bytes spill into the next is still
# found whole: a chunk only yields matches inside its own owned span, and any match starting
# in its un-owned trailing bytes is yielded solely by the following chunk, which re-searches
# that span, so no match is double-counted.
_ZERO_MARKER = 1
_IN_RANGE_MARKER = 2
_CHUNK_BYTES = 1024


def _build_marker_table(personality_range: tuple[int, int]) -> bytes:
    lowest, highest = personality_range
    table = bytearray(256)
    table[0] = _ZERO_MARKER
    for value in range(lowest, highest + 1):
        table[value] = _IN_RANGE_MARKER
    return bytes(table)


def _build_marker_needle(personality_count: int) -> bytes:
    return bytes([_ZERO_MARKER]) + bytes([_IN_RANGE_MARKER]) * personality_count


def iter_marker_run_starts(
    game_db: bytes, search_start: int, window_end: int, marker_table: bytes, needle: bytes
) -> Iterator[int]:
    """Yield each personality run's leading zero-byte position in `[search_start, window_end)`,
    ascending, equivalent to `re.finditer(rb"\\x00[low-high]{count}", game_db, search_start,
    window_end)` but built from `_CHUNK_BYTES`-sized, overlapping, transient chunk
    translations instead of a regex or a save-wide buffer.
    """
    needle_length = len(needle)
    overlap = needle_length - 1
    step = _CHUNK_BYTES - overlap
    position = search_start
    while position < window_end:
        chunk_end = min(position + _CHUNK_BYTES, window_end)
        is_final_chunk = chunk_end == window_end
        owned_limit = (chunk_end - position) if is_final_chunk else step
        translated_chunk = game_db[position:chunk_end].translate(marker_table)
        local_position = 0
        while True:
            local_match = translated_chunk.find(needle, local_position)
            if local_match < 0 or local_match >= owned_limit:
                break
            yield position + local_match
            local_position = local_match + 1
        if is_final_chunk:
            return
        position += step


def _trait_codes() -> tuple[CodedValue[Trait], ...]:
    return tuple(CodedValue.from_raw(Trait, bit) for bit in range(_TRAIT_BIT_COUNT))


def _build_relation_entry_format(layout: PersonBlockLayout) -> str:
    """One relation entry's struct format body (no byte-order prefix), padded to the entry size.

    Raises:
        ValueError: Two relation entry fields overlap, a field starts before the entry start,
            the layout's positions put the fields out of the order they are unpacked (referenced
            value, kind and role, qualifier, sentinel), or the fields run past
            `relation_entry_bytes`.
    """
    fields = [
        (layout.relation_referenced_offset_in_entry, "I", "referenced"),
        (layout.relation_kind_role_offset_in_entry, "H", "kind_role"),
        (layout.relation_qualifier_offset_in_entry, "B", "qualifier"),
        (layout.relation_sentinel_offset_in_entry, "B", "sentinel"),
    ]
    for offset, _format_code, field_name in fields:
        if offset < 0:
            raise ValueError(
                f"relation entry field {field_name!r} at offset {offset} starts before the entry "
                "start"
            )
    struct_object, _start_offset, index_by_name = build_gap_padded_struct(fields, start_offset=0)
    layout_order = tuple(sorted(index_by_name, key=index_by_name.__getitem__))
    if layout_order != _RELATION_FIELD_ORDER:
        raise ValueError(
            "the relation entry fields must be laid out in the order they are unpacked "
            f"({', '.join(_RELATION_FIELD_ORDER)}), but the layout orders them "
            f"{', '.join(layout_order)}"
        )
    padding_bytes = layout.relation_entry_bytes - struct_object.size
    if padding_bytes < 0:
        raise ValueError(
            f"the relation entry fields need {struct_object.size} bytes, more than "
            f"relation_entry_bytes ({layout.relation_entry_bytes})"
        )
    entry_format = struct_object.format
    if isinstance(entry_format, bytes):
        entry_format = entry_format.decode("ascii")
    entry_body = entry_format.removeprefix("<")
    return entry_body + (f"{padding_bytes}x" if padding_bytes else "")


@functools.cache
def _relation_structs_by_count(entry_format: str) -> tuple[struct.Struct, ...]:
    """One struct per possible relation-entry count (0..255, the full range of a stored byte)."""
    return tuple(struct.Struct("<" + entry_format * count) for count in range(256))


def _build_birth_offset_struct(layout: PersonBlockLayout) -> struct.Struct:
    """One struct, starting at the birth-date offset `p`, spanning through the relation count
    byte: nation id, personality, relation present and count, gaps padded from the layout.
    """
    fields: list[tuple[int, str, str]] = [
        (layout.nation_id_offset_from_birth, "H", "nation_id"),
        (layout.personality_offset_from_birth, f"{layout.personality_count}s", "personality"),
        (layout.relation_present_offset_from_birth, "B", "relation_present"),
        (layout.relation_count_offset_from_birth, "B", "relation_count"),
    ]
    struct_object, _start_offset, _index_by_name = build_gap_padded_struct(fields, start_offset=0)
    return struct_object


@dataclass(slots=True)
class PersonBlockDecoder:
    """Decodes person blocks for one save; built once per `players()` call.

    Every offset the hot path (`_try_candidate` and the methods it calls) uses is bound here
    as a plain field, computed once from the layout at build time: no method below loads a
    `layout` attribute. The per-save caches (birth date/age by the raw stored birth word,
    first and last names by pool id) are keyed by values shared across many players.
    `Personality` objects are never cached: they are cheap to build and each one is
    genuinely distinct per player.
    """

    name_pools: NamePools
    first_name_pool: PoolIndex
    surname_pool: PoolIndex
    club_index: ClubIndex
    clock: date
    clock_year: int
    trait_codes: tuple[CodedValue[Trait], ...]
    file_name: str

    # Search.
    marker_table: bytes
    marker_needle: bytes
    zero_offset_from_birth: int

    # Candidate validation and name-block offsets.
    date_zero_bytes_offset: int
    zero_region_bytes: bytes
    legal_name_length_min: int
    legal_name_length_max: int
    legal_name_offset_from_block_start: int
    trait_bits_offset_from_block_start: int
    name_id_limit: int

    # Nation, personality, relation present/count.
    nation_offset: int
    personality_offset: int
    personality_count: int
    relation_present_offset: int
    relation_count_offset: int
    relation_entries_offset: int
    relation_entry_bytes: int
    p_struct: struct.Struct
    p_struct_size: int

    # Relations.
    relation_structs_by_count: tuple[struct.Struct, ...]
    second_nation_qualifiers: tuple[int, ...]
    relation_sentinel_value: int
    second_nation_key: int
    home_grown_nation_key: int
    home_grown_club_key: int

    # Caches.
    birth_cache: dict[int, tuple[date | None, int | None]]
    first_name_cache: dict[int, str | None]
    surname_cache: dict[int, str | None]

    # Counts for the player checks, added to as relation lists are read.
    last_block_start: int | None = None
    relation_entry_count: int = 0
    relation_sentinel_ok_count: int = 0
    second_nation_entry_count: int = 0
    second_nation_qualifier_ok_count: int = 0

    def decode(self, game_db: bytes, window_start: int, window_end: int) -> PersonTuple | None:
        """The first validated person block in `[window_start, window_end)`, or None.

        Raises:
            CorruptSaveError: A validated block's relation header or entry list runs past
                window_end, or its legal name is not valid UTF-8.
        """
        self.last_block_start = None
        search_start = window_start + self.zero_offset_from_birth
        for zero_position in iter_marker_run_starts(
            game_db, search_start, window_end, self.marker_table, self.marker_needle
        ):
            birth_date_offset = zero_position - self.zero_offset_from_birth
            person = self._try_candidate(game_db, birth_date_offset, window_end)
            if person is not None:
                return person
        return None

    def _try_candidate(
        self, game_db: bytes, birth_date_offset: int, window_end: int
    ) -> PersonTuple | None:
        raw_birth_word: int = _BIRTH_WORD_STRUCT.unpack_from(game_db, birth_date_offset)[0]
        packed = raw_birth_word & 0xFFFF
        year = raw_birth_word >> 16
        if packed >> TIME_SLOT_SHIFT != 0:
            return None
        day_of_year = packed & DAY_OF_YEAR_MASK
        if not 1 <= day_of_year <= 366:
            return None
        if not EARLIEST_GAME_YEAR <= year <= self.clock_year:
            return None

        zero_region_offset = birth_date_offset + self.date_zero_bytes_offset
        if not game_db.startswith(self.zero_region_bytes, zero_region_offset):
            return None

        # Legal-name length: inline the common (no legal name) fast path.
        zero_length_word_at = birth_date_offset - 4
        if zero_length_word_at < 0:
            return None
        if _UINT32_STRUCT.unpack_from(game_db, zero_length_word_at)[0] == 0:
            legal_name_length = 0
        else:
            found_length = self._find_legal_name_length(game_db, birth_date_offset)
            if found_length is None:
                return None
            legal_name_length = found_length

        block_start_offset = (
            birth_date_offset - self.legal_name_offset_from_block_start - legal_name_length
        )
        name_block_offset = block_start_offset + self.trait_bits_offset_from_block_start
        if name_block_offset < 0:
            return None
        (
            trait_bits,
            first_name_id,
            first_name_zero,
            surname_id,
            surname_zero,
            common_name_id,
            common_name_zero,
        ) = cast(
            "tuple[int, int, int, int, int, int, int]",
            _NAME_BLOCK_STRUCT.unpack_from(game_db, name_block_offset),
        )
        if first_name_zero or surname_zero or common_name_zero:
            return None
        name_id_limit = self.name_id_limit
        if (
            (first_name_id != MISSING_REFERENCE and first_name_id >= name_id_limit)
            or (surname_id != MISSING_REFERENCE and surname_id >= name_id_limit)
            or (common_name_id != MISSING_REFERENCE and common_name_id >= name_id_limit)
        ):
            return None

        # Birth date and age: inline the cache-hit fast path.
        birth_cache = self.birth_cache
        cached_birth = birth_cache.get(raw_birth_word)
        if cached_birth is not None:
            birth_date, age = cached_birth
        else:
            birth_date = decode_date(game_db, birth_date_offset)
            if birth_date is None:
                age = None
            else:
                clock = self.clock
                age = (
                    clock.year
                    - birth_date.year
                    - ((clock.month, clock.day) < (birth_date.month, birth_date.day))
                )
            birth_cache[raw_birth_word] = (birth_date, age)

        nation_id, personality_bytes, present, relation_count = (
            self._read_nation_personality_present_count(game_db, birth_date_offset, window_end)
        )
        personality = Personality(*personality_bytes)

        # Relations: inline the present-or-count-zero fast path.
        if present == 0 or relation_count == 0:
            second_nation_ids: tuple[int, ...] = ()
            home_grown_nation_ids: tuple[int, ...] = ()
            home_grown_club_uids: tuple[int | None, ...] = ()
            home_grown_club_names: tuple[str | None, ...] = ()
        else:
            (
                second_nation_ids,
                home_grown_nation_ids,
                home_grown_club_uids,
                home_grown_club_names,
            ) = self._read_relation_entries(game_db, birth_date_offset, relation_count, window_end)

        # First and last names: inline the cache-hit fast path.
        first_name_cache = self.first_name_cache
        cached_first_name = first_name_cache.get(first_name_id, _NAME_CACHE_MISS)
        if cached_first_name is not _NAME_CACHE_MISS:
            first_name = cast("str | None", cached_first_name)
        else:
            first_name = self.first_name_pool.name_at(game_db, first_name_id)
            first_name_cache[first_name_id] = first_name

        surname_cache = self.surname_cache
        cached_surname = surname_cache.get(surname_id, _NAME_CACHE_MISS)
        if cached_surname is not _NAME_CACHE_MISS:
            last_name = cast("str | None", cached_surname)
        else:
            last_name = self.surname_pool.name_at(game_db, surname_id)
            surname_cache[surname_id] = last_name

        common_name = (
            None
            if common_name_id == MISSING_REFERENCE
            else self._resolve_common_name(game_db, common_name_id)
        )
        legal_name_start = block_start_offset + self.legal_name_offset_from_block_start
        legal_name = self._decode_legal_name(game_db, legal_name_start, legal_name_length)

        if first_name is not None and last_name is not None:
            full_name = f"{first_name} {last_name}"
            joined_name = f"{first_name} {last_name}"
        elif first_name is not None:
            full_name = None
            joined_name = first_name
        elif last_name is not None:
            full_name = None
            joined_name = last_name
        else:
            full_name = None
            joined_name = None

        if common_name is not None:
            name = common_name
        elif joined_name is not None:
            name = joined_name
        else:
            name = legal_name

        # Traits: inline the zero-bits fast path.
        if trait_bits == 0:
            traits: tuple[CodedValue[Trait], ...] = ()
        else:
            trait_codes = self.trait_codes
            traits_list: list[CodedValue[Trait]] = []
            remaining = trait_bits
            while remaining:
                lowest_set_bit = remaining & -remaining
                traits_list.append(trait_codes[lowest_set_bit.bit_length() - 1])
                remaining ^= lowest_set_bit
            traits = tuple(traits_list)

        self.last_block_start = block_start_offset
        return (
            name,
            first_name,
            last_name,
            common_name,
            full_name,
            legal_name,
            birth_date,
            age,
            nation_id,
            second_nation_ids,
            home_grown_nation_ids,
            home_grown_club_uids,
            home_grown_club_names,
            personality,
            trait_bits,
            traits,
        )

    def _read_nation_personality_present_count(
        self, game_db: bytes, birth_date_offset: int, window_end: int
    ) -> tuple[int, bytes, int, int]:
        """(nation_id, personality_bytes, present, count).

        The fast path reads all four with one guarded Struct; the slow path (the window ends
        before the count byte) reads nation and personality directly (always in bounds: the
        search guarantees the personality run itself fits the window) and raises the same
        `CorruptSaveError` as the entries read below when the present byte lies past
        window_end, or, when present is non-zero, when the count byte does.

        Raises:
            CorruptSaveError: On the slow path, when the present byte lies past window_end,
                or, when present is non-zero, when the count byte does.
        """
        if birth_date_offset + self.p_struct_size <= window_end:
            return self.p_struct.unpack_from(game_db, birth_date_offset)

        nation_id: int = _UINT16_STRUCT.unpack_from(
            game_db, birth_date_offset + self.nation_offset
        )[0]
        personality_start = birth_date_offset + self.personality_offset
        personality_bytes = game_db[personality_start : personality_start + self.personality_count]

        present_offset = birth_date_offset + self.relation_present_offset
        present_header_end = present_offset + 1
        if present_header_end > window_end:
            raise self._relation_overrun_error(present_header_end, window_end)
        present = game_db[present_offset]
        if present == 0:
            return nation_id, personality_bytes, present, 0

        count_offset = birth_date_offset + self.relation_count_offset
        count_header_end = count_offset + 1
        if count_header_end > window_end:
            raise self._relation_overrun_error(count_header_end, window_end)
        count = game_db[count_offset]
        return nation_id, personality_bytes, present, count

    def _find_legal_name_length(self, game_db: bytes, birth_date_offset: int) -> int | None:
        legal_name_length_min = self.legal_name_length_min
        legal_name_length_max = self.legal_name_length_max
        for candidate_length in range(legal_name_length_min, legal_name_length_max + 1):
            length_word_at = birth_date_offset - 4 - candidate_length
            if length_word_at < 0:
                return None
            stored_length: int = _UINT32_STRUCT.unpack_from(game_db, length_word_at)[0]
            if stored_length == candidate_length:
                return candidate_length
        return None

    def _decode_legal_name(
        self, game_db: bytes, legal_name_start: int, legal_name_length: int
    ) -> str | None:
        if legal_name_length == 0:
            return None
        raw_bytes = game_db[legal_name_start : legal_name_start + legal_name_length]
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CorruptSaveError(
                f"{section_label(self.file_name)}: a legal name at offset {legal_name_start} "
                "is not valid UTF-8"
            ) from error

    def _resolve_common_name(self, game_db: bytes, common_name_id: int) -> str | None:
        name_pools = self.name_pools
        for pool in (name_pools.common_names, name_pools.first_names, name_pools.surnames):
            resolved = pool.name_at(game_db, common_name_id)
            if resolved is not None:
                return resolved
        return None

    def _read_relation_entries(
        self, game_db: bytes, birth_date_offset: int, relation_count: int, window_end: int
    ) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int | None, ...], tuple[str | None, ...]]:
        """Called only once `present` and `relation_count` are both known non-zero."""
        entries_start = birth_date_offset + self.relation_entries_offset
        entries_end = entries_start + self.relation_entry_bytes * relation_count
        if entries_end > window_end:
            raise self._relation_overrun_error(entries_end, window_end)

        flat_values = self.relation_structs_by_count[relation_count].unpack_from(
            game_db, entries_start
        )
        second_nation_ids: list[int] = []
        home_grown_nation_ids: list[int] = []
        home_grown_club_uids: list[int | None] = []
        home_grown_club_names: list[str | None] = []
        seen_home_grown_club_referenced: list[int] = []
        second_nation_key = self.second_nation_key
        home_grown_nation_key = self.home_grown_nation_key
        home_grown_club_key = self.home_grown_club_key
        club_index = self.club_index

        second_nation_qualifiers = self.second_nation_qualifiers
        second_nation_entry_count = 0
        second_nation_qualifier_ok_count = 0
        values_iterator = iter(flat_values)
        for referenced, pair_key, qualifier, _sentinel in zip(
            values_iterator, values_iterator, values_iterator, values_iterator, strict=True
        ):
            if pair_key == second_nation_key:
                second_nation_entry_count += 1
                if qualifier in second_nation_qualifiers:
                    second_nation_qualifier_ok_count += 1
                if referenced not in second_nation_ids:
                    second_nation_ids.append(referenced)
            elif pair_key == home_grown_nation_key:
                if referenced not in home_grown_nation_ids:
                    home_grown_nation_ids.append(referenced)
            elif (
                pair_key == home_grown_club_key
                and referenced not in seen_home_grown_club_referenced
            ):
                seen_home_grown_club_referenced.append(referenced)
                club_uid = club_index.uid_by_club_index.get(referenced)
                club = None if club_uid is None else club_index.club_by_uid.get(club_uid)
                home_grown_club_uids.append(club_uid)
                home_grown_club_names.append(None if club is None else club.name)
        self.relation_entry_count += relation_count
        self.relation_sentinel_ok_count += flat_values[
            _RELATION_SENTINEL_INDEX::_RELATION_VALUES_PER_ENTRY
        ].count(self.relation_sentinel_value)
        if second_nation_entry_count:
            self.second_nation_entry_count += second_nation_entry_count
            self.second_nation_qualifier_ok_count += second_nation_qualifier_ok_count
        return (
            tuple(second_nation_ids) if second_nation_ids else (),
            tuple(home_grown_nation_ids) if home_grown_nation_ids else (),
            tuple(home_grown_club_uids) if home_grown_club_uids else (),
            tuple(home_grown_club_names) if home_grown_club_names else (),
        )

    def _relation_overrun_error(self, needed_end: int, window_end: int) -> CorruptSaveError:
        return CorruptSaveError(
            f"{section_label(self.file_name)}: a player's relation list needs bytes up to "
            f"offset {needed_end}, past the record window ending at {window_end}"
        )


def build_person_block_decoder(
    layout: PersonBlockLayout,
    name_pools: NamePools,
    club_index: ClubIndex,
    clock: date,
    file_name: str,
) -> PersonBlockDecoder:
    """Build the per-save person-block decoder from the save's layout, indexes and clock.

    Raises:
        ValueError: The layout's relation entry positions are inconsistent (see
            `_build_relation_entry_format`).
    """
    second_nation_key = (layout.second_nation_pair[1] << 8) | layout.second_nation_pair[0]
    home_grown_nation_key = (layout.home_grown_nation_pair[1] << 8) | layout.home_grown_nation_pair[
        0
    ]
    home_grown_club_key = (layout.home_grown_club_pair[1] << 8) | layout.home_grown_club_pair[0]
    p_struct = _build_birth_offset_struct(layout)
    return PersonBlockDecoder(
        name_pools=name_pools,
        first_name_pool=name_pools.first_names,
        surname_pool=name_pools.surnames,
        club_index=club_index,
        clock=clock,
        clock_year=clock.year,
        trait_codes=_trait_codes(),
        file_name=file_name,
        marker_table=_build_marker_table(layout.personality_range),
        marker_needle=_build_marker_needle(layout.personality_count),
        zero_offset_from_birth=layout.personality_offset_from_birth - 1,
        date_zero_bytes_offset=layout.date_zero_bytes_offset_from_birth,
        zero_region_bytes=bytes(layout.date_zero_bytes_count),
        legal_name_length_min=layout.legal_name_length_min,
        legal_name_length_max=layout.legal_name_length_max,
        legal_name_offset_from_block_start=layout.legal_name_offset_from_block_start,
        trait_bits_offset_from_block_start=layout.trait_bits_offset_from_block_start,
        name_id_limit=layout.name_id_limit,
        nation_offset=layout.nation_id_offset_from_birth,
        personality_offset=layout.personality_offset_from_birth,
        personality_count=layout.personality_count,
        relation_present_offset=layout.relation_present_offset_from_birth,
        relation_count_offset=layout.relation_count_offset_from_birth,
        relation_entries_offset=layout.relation_entries_offset_from_birth,
        relation_entry_bytes=layout.relation_entry_bytes,
        p_struct=p_struct,
        p_struct_size=p_struct.size,
        relation_structs_by_count=_relation_structs_by_count(_build_relation_entry_format(layout)),
        second_nation_qualifiers=layout.second_nation_qualifiers,
        relation_sentinel_value=layout.relation_sentinel_value,
        second_nation_key=second_nation_key,
        home_grown_nation_key=home_grown_nation_key,
        home_grown_club_key=home_grown_club_key,
        birth_cache={},
        first_name_cache={},
        surname_cache={},
    )
