"""Locating player records in `game_db`: the marker and completeness scans, and acceptance.

Player records are found by two scans: a fast marker anchor, and a slower completeness pass
over the region after the name pools that catches records the anchor scan misses. Results
from both passes are merged in ascending record-offset order into a private index,
`PlayerRecords`. `readers/players.py` decodes the records this module locates; it imports
from here, never the other way around.
"""

from __future__ import annotations

import functools
import re
import struct
from array import array
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from fm26save._core._errors import CorruptSaveError
from fm26save._core._layouts import PlayerRecordLayout
from fm26save._core.readers._common import (
    MISSING_REFERENCE,
    build_gap_padded_struct,
    layout_mismatch,
    section_label,
)

RECORD_OFFSET_TYPECODE = "Q"
PINDEX_TYPECODE = "I"
UID_TYPECODE = "I"
PLAYER_RECORDS_CACHE_KEY = "player_records"

type _Candidate = tuple[int, int, int]  # (record_offset, pindex, uid)


def _record_overrun(file_name: str) -> CorruptSaveError:
    return CorruptSaveError(
        f"{section_label(file_name)}: a player record runs past the end of the section"
    )


@dataclass(frozen=True, slots=True, repr=False)
class PlayerRecords:
    """Every accepted player record's offset, pindex and uid, in ascending record offset.

    Never mutate the mappings: this index is cached and shared by every reader of a save.

    Attributes:
        record_offsets: Each record's start offset in `game_db`, ascending.
        pindexes: Each record's pindex, aligned with record_offsets.
        uids: Each record's uid, aligned with record_offsets.
        markerless_count: How many records were found only by the completeness pass.
        position_by_pindex: Position in the arrays above for each pindex.
        position_by_uid: Position in the arrays above for each uid.
        layout: The layout the scan used, for building a PlayerDecoder.
    """

    record_offsets: array[int]
    pindexes: array[int]
    uids: array[int]
    markerless_count: int
    position_by_pindex: Mapping[int, int]
    position_by_uid: Mapping[int, int]
    layout: PlayerRecordLayout

    def __repr__(self) -> str:
        return f"<fmsave PlayerRecords {len(self.record_offsets)} records>"


def locate_player_records(
    game_db: bytes, name_pools_end: int, layout: PlayerRecordLayout, file_name: str
) -> PlayerRecords:
    """Scan `game_db` for player records with both the marker and completeness passes.

    Raises:
        ReaderCheckError: No player records were found, or a pindex or uid appears in two
            records.
        CorruptSaveError: An accepted record runs past the end of `game_db`.
    """
    uid_layout = _uid_layout(layout)
    header_layout = build_header_layout(layout)
    pattern = _completeness_pattern(
        layout.rating_range,
        layout.ratings_count,
        _scan_attribute_range(layout),
        layout.attribute_count,
    )
    marker_candidates = _scan_marker_candidates(
        game_db, layout, uid_layout, header_layout, pattern, file_name
    )
    marker_offsets = {candidate[0] for candidate in marker_candidates}
    completeness_candidates = _scan_completeness_candidates(
        game_db,
        name_pools_end,
        layout,
        uid_layout,
        header_layout,
        pattern,
        marker_offsets,
        file_name,
    )
    merged = marker_candidates + completeness_candidates
    merged.sort(key=lambda candidate: candidate[0])
    if not merged:
        raise layout_mismatch(file_name, "no player records found")
    _reject_repeated_keys(merged, file_name)
    record_offsets = array(RECORD_OFFSET_TYPECODE, (candidate[0] for candidate in merged))
    pindexes = array(PINDEX_TYPECODE, (candidate[1] for candidate in merged))
    uids = array(UID_TYPECODE, (candidate[2] for candidate in merged))
    position_by_pindex = {pindex: position for position, pindex in enumerate(pindexes)}
    position_by_uid = {uid: position for position, uid in enumerate(uids)}
    return PlayerRecords(
        record_offsets=record_offsets,
        pindexes=pindexes,
        uids=uids,
        markerless_count=len(completeness_candidates),
        position_by_pindex=position_by_pindex,
        position_by_uid=position_by_uid,
        layout=layout,
    )


def window_end(records: PlayerRecords, position: int, game_db_length: int) -> int:
    """The offset ending the window of the record at position: the next record's start, or
    the length of `game_db` for the last record.
    """
    next_position = position + 1
    if next_position < len(records.record_offsets):
        return records.record_offsets[next_position]
    return game_db_length


_CLOSING_HEADER = struct.Struct("<III")
_LAST_PERSON_ID = 0xFFFFFFFF


def closing_person_header(
    game_db: bytes,
    person_id: int,
    search_start: int,
    search_end: int,
    uid_floor: int,
    uid_ceiling: int | None,
) -> tuple[int, int] | None:
    """The (offset, database Unique ID) of the unique header closing this person, or None.

    It is the doubled uid of the sound header that carries `person_id + 1`, the id the save's
    references use for him, and that closes his object. That header is looked for with its id
    starting in `[search_start, search_end)`, and it counts only when its uid is above
    `uid_floor` (his own header's uid) and not above `uid_ceiling` (the next known header's
    uid), since objects are stored in ascending uid order. None unless exactly one header
    passes.
    """
    if person_id >= _LAST_PERSON_ID:
        return None
    needle = struct.pack("<I", person_id + 1)
    last_start = len(game_db) - _CLOSING_HEADER.size
    find = game_db.find
    found: tuple[int, int] | None = None
    hit = find(needle, search_start, search_end)
    while 0 <= hit <= last_start:
        _, uid, uid_copy = _CLOSING_HEADER.unpack_from(game_db, hit)
        if (
            uid == uid_copy
            and uid != MISSING_REFERENCE
            and uid > uid_floor
            and (uid_ceiling is None or uid <= uid_ceiling)
        ):
            if found is not None:
                return None
            found = (hit, uid)
        hit = find(needle, hit + 1, search_end)
    return found


def closing_unique_id(
    game_db: bytes,
    person_id: int,
    search_start: int,
    search_end: int,
    uid_floor: int,
    uid_ceiling: int | None,
) -> int | None:
    """The database Unique ID from the unique validated closing-person header, or None."""
    closing = closing_person_header(
        game_db, person_id, search_start, search_end, uid_floor, uid_ceiling
    )
    return None if closing is None else closing[1]


def _reject_repeated_keys(candidates: Sequence[_Candidate], file_name: str) -> None:
    seen_pindexes: set[int] = set()
    seen_uids: set[int] = set()
    for _, pindex, uid in candidates:
        if pindex in seen_pindexes:
            raise layout_mismatch(file_name, f"pindex {pindex} appears in two player records")
        if uid in seen_uids:
            raise layout_mismatch(file_name, f"player uid {uid} appears in two player records")
        seen_pindexes.add(pindex)
        seen_uids.add(uid)


def _scan_marker_candidates(
    game_db: bytes,
    layout: PlayerRecordLayout,
    uid_layout: _UidLayout,
    header_layout: HeaderLayout,
    pattern: re.Pattern[bytes],
    file_name: str,
) -> list[_Candidate]:
    """Every record found by the marker anchor, in the order the anchor is found."""
    buffer_length = len(game_db)
    find_marker = game_db.find
    marker = layout.marker
    marker_offset = layout.marker_offset
    decode_extent = layout.decode_extent
    candidates: list[_Candidate] = []
    marker_hit = find_marker(marker, 0)
    while marker_hit >= 0:
        record_offset = marker_hit - marker_offset
        accepted = _accept_candidate(
            game_db,
            record_offset,
            layout,
            buffer_length,
            uid_layout,
            header_layout,
            pattern,
            check_pattern=True,
        )
        if accepted is not None:
            if record_offset + decode_extent > buffer_length:
                raise _record_overrun(file_name)
            candidates.append((record_offset, *accepted))
        marker_hit = find_marker(marker, marker_hit + 1)
    return candidates


def _scan_completeness_candidates(
    game_db: bytes,
    name_pools_end: int,
    layout: PlayerRecordLayout,
    uid_layout: _UidLayout,
    header_layout: HeaderLayout,
    pattern: re.Pattern[bytes],
    marker_offsets: set[int],
    file_name: str,
) -> list[_Candidate]:
    """Every record found by the 69-byte ratings-then-attributes pattern, offset ascending.

    Uses `_flagged_runs` to bound the exact pattern search to the (rare) stretches of bytes
    that could possibly hold a match, instead of scanning the whole post-name-pools region.
    """
    buffer_length = len(game_db)
    decode_extent = layout.decode_extent
    ratings_offset = layout.ratings_offset
    minimum_run_length = layout.ratings_count + layout.attribute_count
    candidates: list[_Candidate] = []
    for run_start, run_end in _flagged_runs(
        game_db,
        name_pools_end,
        layout.rating_range,
        _scan_attribute_range(layout),
        minimum_run_length,
    ):
        for match in pattern.finditer(game_db, run_start, run_end):
            record_offset = match.start() - ratings_offset
            if record_offset in marker_offsets:
                continue
            accepted = _accept_candidate(
                game_db,
                record_offset,
                layout,
                buffer_length,
                uid_layout,
                header_layout,
                pattern,
                check_pattern=False,
            )
            if accepted is not None:
                if record_offset + decode_extent > buffer_length:
                    raise _record_overrun(file_name)
                candidates.append((record_offset, *accepted))
    return candidates


def _flagged_runs(
    buffer: bytes,
    start: int,
    rating_range: tuple[int, int],
    attribute_range: tuple[int, int],
    minimum_run_length: int,
) -> Iterator[tuple[int, int]]:
    """Yield (run_start, run_end) for each maximal run, at or after start, of at least
    minimum_run_length consecutive bytes that lie in the hull of the two ranges: the smallest
    single range containing both, and so a superset of each regex byte class.

    A translate table flags each byte 1 when it lies in that hull, 0 otherwise.
    `flags.find(run_needle, position)`, where run_needle is minimum_run_length flag bytes of
    1, finds the first index at or after position where a run of that many flagged bytes
    starts. That index is exact: an earlier start in the same maximal run would itself be a
    valid needle match, so `find` (which returns the first match) would have returned it
    instead, which means no qualifying run is ever skipped. `flags.find(b"\\x00", ...)` from
    just past that needle then finds where the same maximal run ends, since every byte before
    the next 0 is, by construction, part of one contiguous flagged stretch.

    A true completeness-pattern match's bytes are all flagged, because both the rating and
    the attribute sub-ranges the pattern checks are subsets of the hull, so every true match
    lies entirely inside one maximal run; bounding the exact search to these runs therefore
    finds the same matches a global, unbounded search would.
    """
    buffer_length = len(buffer)
    flags = buffer.translate(_flag_table(rating_range, attribute_range))
    run_needle = _run_needle(minimum_run_length)
    find_in_flags = flags.find
    position = start
    while True:
        run_start = find_in_flags(run_needle, position)
        if run_start < 0:
            break
        run_end = find_in_flags(b"\x00", run_start + minimum_run_length)
        if run_end < 0:
            run_end = buffer_length
        yield run_start, run_end
        position = run_end
    del flags


@functools.cache
def _flag_table(rating_range: tuple[int, int], attribute_range: tuple[int, int]) -> bytes:
    """256-byte translate table: 1 for a byte inside either range, 0 outside both."""
    lowest = min(rating_range[0], attribute_range[0])
    highest = max(rating_range[1], attribute_range[1])
    return bytes(1 if lowest <= value <= highest else 0 for value in range(256))


@functools.cache
def _run_needle(minimum_run_length: int) -> bytes:
    return b"\x01" * minimum_run_length


def _accept_candidate(
    game_db: bytes,
    record_offset: int,
    layout: PlayerRecordLayout,
    buffer_length: int,
    uid_layout: _UidLayout,
    header_layout: HeaderLayout,
    pattern: re.Pattern[bytes],
    *,
    check_pattern: bool,
) -> tuple[int, int] | None:
    """Check one candidate; return (pindex, uid) when every acceptance check holds, else None.

    check_pattern is False for a completeness-pass candidate, whose ratings and attribute
    bytes the regex has already validated at this exact position. Identity checks run first
    from their own small struct; allocated headers with a distinct second identity word also
    require the player object kind. The wider header and full attribute checks still apply.
    """
    header_absolute_start = record_offset + header_layout.start_offset
    accept_checks_end = record_offset + max(
        layout.attributes_offset + layout.attribute_count, layout.object_kind_offset + 1
    )
    if (
        header_absolute_start < 0
        or record_offset + layout.object_kind_offset < 0
        or accept_checks_end > buffer_length
    ):
        return None
    uid_values = uid_layout.struct_object.unpack_from(
        game_db, record_offset + uid_layout.start_offset
    )
    uid: int = uid_values[uid_layout.uid_index]
    uid_copy: int = uid_values[uid_layout.uid_copy_index]
    if uid in (0, MISSING_REFERENCE) or uid_copy in (0, MISSING_REFERENCE):
        return None
    if uid != uid_copy and (
        uid < layout.allocated_uid_minimum
        or game_db[record_offset + layout.object_kind_offset] not in layout.player_kinds
    ):
        return None
    header_values = header_layout.struct_object.unpack_from(game_db, header_absolute_start)
    current_ability: int = header_values[header_layout.current_ability_index]
    lowest_ability, highest_ability = layout.current_ability_range
    potential_ability: int = header_values[header_layout.potential_ability_index]
    lowest_potential, highest_potential = layout.potential_ability_range
    raw_attributes = game_db[
        record_offset + layout.attributes_offset : record_offset
        + layout.attributes_offset
        + layout.attribute_count
    ]
    needs_edited_ranges = (
        current_ability > highest_ability
        or potential_ability > highest_potential
        or max(raw_attributes) > layout.attribute_range[1]
    )
    if needs_edited_ranges:
        if (
            layout.edited_ability_maximum is None
            or layout.edited_attribute_maximum is None
            or uid != uid_copy
            or game_db[record_offset + layout.object_kind_offset] not in layout.player_kinds
        ):
            return None
        highest_ability = layout.edited_ability_maximum
        highest_potential = layout.edited_ability_maximum
    if not (
        lowest_ability <= current_ability <= highest_ability
        and lowest_potential <= potential_ability <= highest_potential
    ):
        return None
    reputation_bucket: int = header_values[header_layout.reputation_bucket_index]
    lowest_bucket, highest_bucket = layout.reputation_bucket_range
    if not lowest_bucket <= reputation_bucket <= highest_bucket:
        return None
    if check_pattern and pattern.match(game_db, record_offset + layout.ratings_offset) is None:
        return None
    pindex: int = header_values[header_layout.pindex_index]
    return pindex, uid


def _byte_class(value_range: tuple[int, int]) -> bytes:
    lowest, highest = value_range
    return b"[" + re.escape(bytes((lowest,))) + b"-" + re.escape(bytes((highest,))) + b"]"


def _scan_attribute_range(layout: PlayerRecordLayout) -> tuple[int, int]:
    """Search a superset; edited candidates also require the independently stored player kind."""
    lowest, highest = layout.attribute_range
    return lowest, max(highest, layout.edited_attribute_maximum or highest)


@functools.cache
def _completeness_pattern(
    rating_range: tuple[int, int],
    ratings_count: int,
    attribute_range: tuple[int, int],
    attribute_count: int,
) -> re.Pattern[bytes]:
    """The compiled pattern for the completeness pass; cached so it is built only once."""
    rating_class = _byte_class(rating_range)
    attribute_class = _byte_class(attribute_range)
    pattern = (
        rating_class
        + b"{"
        + str(ratings_count).encode("ascii")
        + b"}"
        + attribute_class
        + b"{"
        + str(attribute_count).encode("ascii")
        + b"}"
    )
    return re.compile(pattern)


@dataclass(frozen=True, slots=True)
class _UidLayout:
    """A small struct covering only uid_offset and uid_copy_offset.

    Most marker-anchor hits are false positives, and almost all of them fail the doubled-uid
    check; reading just these two fields first, before the wider header struct, skips
    unpacking the other eight header fields for a candidate that is about to be rejected.
    """

    struct_object: struct.Struct
    start_offset: int
    uid_index: int
    uid_copy_index: int


@dataclass(frozen=True, slots=True)
class HeaderLayout:
    """A struct spanning pindex_offset..team_id_offset+4, and each field's tuple index."""

    struct_object: struct.Struct
    start_offset: int
    pindex_index: int
    uid_index: int
    uid_copy_index: int
    home_reputation_index: int
    current_reputation_index: int
    world_reputation_index: int
    current_ability_index: int
    potential_ability_index: int
    reputation_bucket_index: int
    team_id_index: int


_UID_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("uid_offset", "I"),
    ("uid_copy_offset", "I"),
)

_HEADER_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("pindex_offset", "I"),
    ("uid_offset", "I"),
    ("uid_copy_offset", "I"),
    ("home_reputation_offset", "H"),
    ("current_reputation_offset", "H"),
    ("world_reputation_offset", "H"),
    ("current_ability_offset", "H"),
    ("potential_ability_offset", "h"),
    ("reputation_bucket_offset", "B"),
    ("team_id_offset", "I"),
)


def indexed_struct(
    layout: PlayerRecordLayout, field_specs: tuple[tuple[str, str], ...]
) -> tuple[struct.Struct, int, dict[str, int]]:
    """One struct spanning every named offset in field_specs, gaps padded, offsets ascending."""
    fields = [(getattr(layout, attr_name), code, attr_name) for attr_name, code in field_specs]
    return build_gap_padded_struct(fields)


@functools.cache
def _uid_layout(layout: PlayerRecordLayout) -> _UidLayout:
    uid_struct, start_offset, index_by_field = indexed_struct(layout, _UID_FIELD_SPECS)
    return _UidLayout(
        struct_object=uid_struct,
        start_offset=start_offset,
        uid_index=index_by_field["uid_offset"],
        uid_copy_index=index_by_field["uid_copy_offset"],
    )


@functools.cache
def build_header_layout(layout: PlayerRecordLayout) -> HeaderLayout:
    header_struct, start_offset, index_by_field = indexed_struct(layout, _HEADER_FIELD_SPECS)
    return HeaderLayout(
        struct_object=header_struct,
        start_offset=start_offset,
        pindex_index=index_by_field["pindex_offset"],
        uid_index=index_by_field["uid_offset"],
        uid_copy_index=index_by_field["uid_copy_offset"],
        home_reputation_index=index_by_field["home_reputation_offset"],
        current_reputation_index=index_by_field["current_reputation_offset"],
        world_reputation_index=index_by_field["world_reputation_offset"],
        current_ability_index=index_by_field["current_ability_offset"],
        potential_ability_index=index_by_field["potential_ability_offset"],
        reputation_bucket_index=index_by_field["reputation_bucket_offset"],
        team_id_index=index_by_field["team_id_offset"],
    )
