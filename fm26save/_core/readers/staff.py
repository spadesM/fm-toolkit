"""The people a club employs who are not players: the club lists, their contracts and objects.

A club record names some of its staff in three lists that follow its affiliated-team ids, but a
fifth of the people a save employs are in no list at all, the human manager among them. So this
reader works from two ends. It walks every club record's lists, and it makes one filtered pass
over `game_db` for contract records whose selector is a person rather than a player; a record
belongs to the person whose header sits in front of it, which is how a person with no listing is
found. The two populations are merged on (club, person), with a person an affiliate side lists
and its parent pays belonging to the parent, the same rule a player on a B team follows.

A person's object holds his abilities, a role-like byte, the preferences a staff profile shows
and his name block; where the object's ability block does not read, nothing from it is shipped.
The human manager's object is laid out differently and is megabytes long, so he is located from
the `humans` section and read on his own.
"""

from __future__ import annotations

import functools
import re
import struct
from bisect import bisect_left
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Final, cast

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import (
    ContractLayout,
    HumansLayout,
    PersonBlockLayout,
    StaffLayout,
    TeamListLayout,
    find_layout,
)
from fm26save._core._reader_stats import StaffStats
from fm26save._core.models.players import Ability
from fm26save._core.models.staff import Staff, StaffAttributes, StaffList, StaffPreferences
from fm26save._core.readers._common import GAME_DB_SECTION, HUMANS_SECTION, build_gap_padded_struct
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.contracts import (
    CHAIN_RECORD_CLUB_UID,
    CHAIN_RECORD_CONTRACT_TYPE,
    CHAIN_RECORD_END,
    CHAIN_RECORD_HAS_TERMS,
    CHAIN_RECORD_SQUAD_STATUS,
    CHAIN_RECORD_START,
    CHAIN_RECORD_TEAM_ID,
    CHAIN_RECORD_UNKNOWN,
    CHAIN_RECORD_WAGE,
    ChainRecordTuple,
    ContractDecoder,
    build_contract_decoder,
)
from fm26save._core.readers.managed import first_human_selector
from fm26save._core.readers.names import NamePools
from fm26save._core.readers.persons import PersonTuple, build_person_block_decoder
from fm26save._core.readers.player_scan import PlayerRecords, closing_unique_id

_UINT32 = struct.Struct("<I")
_UINT16 = struct.Struct("<H")
_INT16 = struct.Struct("<h")
_MISSING_UID = 0xFFFFFFFF
# A list value and a chain selector are a person id plus one.
_ID_OFFSET = 1
# The tail fields a staff contract keeps that no displayed label has named, under the keys they
# ship as. The first comes from the tuple position a player's squad status is read from and is
# never a `SquadStatus`; the other three come from the tail's own unknown map.
_CONTRACT_STATUS_KEY = "contract_e36"
_CONTRACT_TAIL_KEYS: Final = (
    ("contract_e37", "e37"),
    ("contract_e38", "e38"),
    ("contract_e39", "e39"),
)
_CONTRACT_TYPE_KEY = "contract_type"
_ENTRY_COUNT_KEY = "entry_count"
_ROLE_KEY = "r4"
# Where each field sits in what `PersonBlockDecoder.decode` returns.
_PERSON_NAME = 0
_PERSON_FIRST_NAME = 1
_PERSON_LAST_NAME = 2
_PERSON_COMMON_NAME = 3
_PERSON_FULL_NAME = 4
_PERSON_LEGAL_NAME = 5
_PERSON_BIRTH_DATE = 6
_PERSON_AGE = 7
_PERSON_NATION_ID = 8
_PERSON_PERSONALITY = 13
# The earliest date a record with no readable start is ordered by, so a person's records still
# sort even when one of them stores a start nothing can read.
_UNDATED_START = date(1, 1, 1)


class _Ambiguous:
    """More than one header in a person's window passes the header test, so none is his."""

    __slots__ = ()


_AMBIGUOUS: Final = _Ambiguous()


@dataclass(frozen=True, slots=True)
class StaffLayouts:
    """The layouts the staff reader uses."""

    staff: StaffLayout
    contracts: ContractLayout
    person_blocks: PersonBlockLayout
    team_lists: TeamListLayout
    humans: HumansLayout


def find_staff_layouts(section_schemas: Mapping[str, int], build: str) -> StaffLayouts:
    """Look up every layout the staff reader needs, falling back to the build."""
    game_db_schema = section_schemas.get(GAME_DB_SECTION)
    return StaffLayouts(
        staff=find_layout(StaffLayout, GAME_DB_SECTION, game_db_schema, build).layout,
        contracts=find_layout(ContractLayout, GAME_DB_SECTION, game_db_schema, build).layout,
        person_blocks=find_layout(PersonBlockLayout, GAME_DB_SECTION, game_db_schema, build).layout,
        team_lists=find_layout(TeamListLayout, GAME_DB_SECTION, game_db_schema, build).layout,
        humans=find_layout(
            HumansLayout, HUMANS_SECTION, section_schemas.get(HUMANS_SECTION), build
        ).layout,
    )


@dataclass(frozen=True, slots=True)
class _HeaderReader:
    """One struct spanning a person header's doubled uid and its object-kind byte."""

    struct_object: struct.Struct
    start_offset: int
    extent: int
    uid_index: int
    uid_copy_index: int
    kind_index: int


@functools.cache
def _header_reader(layout: StaffLayout) -> _HeaderReader:
    """The layout's header struct, built on first use for each layout.

    Raises:
        ValueError: Two header fields overlap, or one starts before the person id.
    """
    header_struct, start_offset, index_by_name = build_gap_padded_struct(
        [
            (layout.uid_offset, "I", "uid"),
            (layout.uid_copy_offset, "I", "uid_copy"),
            (layout.kind_offset, "B", "kind"),
        ]
    )
    return _HeaderReader(
        struct_object=header_struct,
        start_offset=start_offset,
        extent=start_offset + header_struct.size,
        uid_index=index_by_name["uid"],
        uid_copy_index=index_by_name["uid_copy"],
        kind_index=index_by_name["kind"],
    )


def _header_values(
    game_db: bytes, header: int, reader: _HeaderReader, layout: StaffLayout | None = None
) -> tuple[int, int] | None:
    """(uid, object kind) of a sound header at `header`, or None when it is not one.

    Ordinary headers repeat the uid; both identity words must be nonzero and not the
    missing-reference word. Allocated staff headers with different identity words
    also need their object kind and complete ability/preference block to match.
    Ten person ids per save have several offsets that pass that
    much, which is why every caller also weighs the object kind.
    """
    if header < 0 or header + reader.extent > len(game_db):
        return None
    values = reader.struct_object.unpack_from(game_db, header + reader.start_offset)
    uid: int = values[reader.uid_index]
    other = values[reader.uid_copy_index]
    kind = values[reader.kind_index]
    if uid in (0, _MISSING_UID) or other in (0, _MISSING_UID):
        return None
    if uid != other:
        if layout is None or uid < layout.allocated_uid_minimum or kind != layout.staff_kind:
            return None
        # The code set is the codes observed, not a closed set (`staff_codes_in_set` is a
        # share for that reason), so a code outside it cannot rule out a header (Refs #20).
        block, slots_ok, _codes_ok, further_ok = _read_ability_block(game_db, header, layout)
        if block is None or not (slots_ok and further_ok):
            return None
    return uid, kind


def locate_contracted_header(
    game_db: bytes, person_id: int, tag_offset: int, layout: StaffLayout
) -> int | None:
    """The offset of a person's own header behind one of his contract records, or None.

    The record lies inside his object, so his header is the nearest sound one with his id in
    front of the tag. The furthest a record measured sits from its header is 8,161 bytes, well
    inside `contract_header_search_bytes`; searching a window wide enough to hold any person
    instead costs about 25 seconds a save.
    """
    return _contract_header_with_kind(game_db, person_id, tag_offset, layout, (layout.staff_kind,))


def _contract_header_with_kind(
    game_db: bytes, person_id: int, tag_offset: int, layout: StaffLayout, kinds: tuple[int, ...]
) -> int | None:
    reader = _header_reader(layout)
    needle = _UINT32.pack(person_id)
    search_start = max(tag_offset - layout.contract_header_search_bytes, 0)
    rfind = game_db.rfind
    hit = rfind(needle, search_start, tag_offset)
    while hit >= 0:
        values = _header_values(game_db, hit, reader, layout)
        if values is not None and values[1] in kinds:
            return hit
        # The end is exclusive, so this still reaches a hit that overlaps the one just tried.
        hit = rfind(needle, search_start, hit + _UINT32.size - 1)
    return None


def _bracket_window(
    game_db: bytes, person_id: int, player_records: PlayerRecords
) -> tuple[int, int]:
    """[start, end) between the player records whose pindexes bracket `person_id`.

    Person ids rise with offset, and the player scan's pindexes are strictly ascending in
    record order, so the two players either side of an id bound where his object can be. The
    window ends at the next player's own header, and at the end of the section when no player
    follows him.
    """
    record_offsets = player_records.record_offsets
    position = bisect_left(player_records.pindexes, person_id)
    window_start = 0 if position == 0 else record_offsets[position - 1]
    if position < len(record_offsets):
        window_end = record_offsets[position] + player_records.layout.pindex_offset
    else:
        window_end = len(game_db)
    return window_start, max(window_end, window_start)


def locate_listed_header(
    game_db: bytes, person_id: int, player_records: PlayerRecords, layout: StaffLayout
) -> int | None | _Ambiguous:
    """The header of a person no contract record points at, `_AMBIGUOUS`, or None.

    A person with no contract has no record to search back from, so his object is looked for
    between the player records that bracket his id. Where more than one offset in that window
    is a sound staff header with his id, none of them can be shown to be his and he is left
    out; the ten ids a save has that of are told apart by the object kind, so this is rare.
    """
    reader = _header_reader(layout)
    staff_kind = layout.staff_kind
    window_start, window_end = _bracket_window(game_db, person_id, player_records)
    needle = _UINT32.pack(person_id)
    find = game_db.find
    located: int | None = None
    hit = find(needle, window_start, window_end)
    while hit >= 0:
        values = _header_values(game_db, hit, reader, layout)
        if values is not None and values[1] == staff_kind:
            if located is not None:
                return _AMBIGUOUS
            located = hit
        hit = find(needle, hit + 1, window_end)
    return located


def locate_human_header(game_db: bytes, selector: int, layout: StaffLayout) -> int | None:
    """The human manager's own header, or None when the section holds no such object.

    His object carries its own kind byte and is megabytes long, so it is found by his id rather
    than by any window: the first sound header of that kind carrying it is his.
    """
    reader = _header_reader(layout)
    human_kind = layout.human_kind
    needle = _UINT32.pack(selector - _ID_OFFSET)
    find = game_db.find
    hit = find(needle)
    while hit >= 0:
        values = _header_values(game_db, hit, reader)
        if values is not None and values[1] == human_kind:
            return hit
        hit = find(needle, hit + 1)
    return None


@dataclass(frozen=True, slots=True)
class _ListCounts:
    """What one pass over the club records' staff lists counted."""

    clubs_checked: int
    clubs_lists_fit: int
    list_values: int
    player_values_in_lists: int
    unset_list_values: int


type _ListedPairs = dict[tuple[int, int], tuple[int, ...]]
type _ListsByClub = dict[int, tuple[tuple[int, ...], ...]]


def read_staff_lists(
    game_db: bytes,
    club_index: ClubIndex,
    player_records: PlayerRecords,
    layout: StaffLayout,
) -> tuple[_ListedPairs, _ListsByClub, _ListCounts]:
    """Every club's staff lists: the (club, person) pairs with their list numbers, the lists
    themselves per club, and what the pass counted.

    A club record holds its affiliated-team ids and then exactly `layout.list_count` lists;
    whatever follows them is other data and is never read as one more. A club's lists are taken
    only when all of them end inside the record and every value lies inside
    `layout.list_value_range` or is zero, which names no person and is counted separately.
    Values that turn out to be player pindexes are dropped and counted, and a person two
    lists of one club both
    name keeps both list numbers.
    """
    pindex_positions = player_records.position_by_pindex
    lowest_value, highest_value = layout.list_value_range
    list_count = layout.list_count
    section_end = len(game_db)
    listed_pairs: dict[tuple[int, int], tuple[int, ...]] = {}
    lists_by_club: dict[int, tuple[tuple[int, ...], ...]] = {}
    clubs_checked = 0
    clubs_lists_fit = 0
    list_values = 0
    player_values_in_lists = 0
    unset_list_values = 0
    for span in club_index.record_spans:
        team_list_end = span.team_list_end
        if team_list_end is None:
            continue
        clubs_checked += 1
        record_end = min(span.record_end, section_end)
        if team_list_end >= record_end:
            continue
        cursor = team_list_end + 1 + _UINT32.size * game_db[team_list_end]
        stored_lists: list[tuple[int, ...]] = []
        for _list_number in range(list_count):
            if cursor >= record_end:
                break
            value_count = game_db[cursor]
            cursor += 1
            values_end = cursor + _UINT32.size * value_count
            if values_end > record_end:
                break
            stored_lists.append(
                tuple(
                    _UINT32.unpack_from(game_db, value_offset)[0]
                    for value_offset in range(cursor, values_end, _UINT32.size)
                )
            )
            cursor = values_end
        if len(stored_lists) != list_count or any(
            value != 0 and not lowest_value <= value <= highest_value
            for stored_list in stored_lists
            for value in stored_list
        ):
            continue
        clubs_lists_fit += 1
        club_uid = span.club_uid
        person_lists: list[tuple[int, ...]] = []
        list_numbers_here: dict[int, list[int]] = {}
        for list_number, stored_list in enumerate(stored_lists):
            list_values += len(stored_list)
            person_ids: list[int] = []
            for value in stored_list:
                # Selectors hold a person index plus one; zero names no person.
                if value == 0:
                    unset_list_values += 1
                    continue
                person_id = value - _ID_OFFSET
                if person_id in pindex_positions:
                    player_values_in_lists += 1
                    continue
                person_ids.append(person_id)
                list_numbers_here.setdefault(person_id, []).append(list_number)
            person_lists.append(tuple(person_ids))
        lists_by_club[club_uid] = tuple(person_lists)
        for person_id, list_numbers in list_numbers_here.items():
            listed_pairs[(club_uid, person_id)] = tuple(list_numbers)
    return (
        listed_pairs,
        lists_by_club,
        _ListCounts(
            clubs_checked=clubs_checked,
            clubs_lists_fit=clubs_lists_fit,
            list_values=list_values,
            player_values_in_lists=player_values_in_lists,
            unset_list_values=unset_list_values,
        ),
    )


def _byte_class(highest: int) -> bytes:
    return b"[\\x00-" + f"\\x{highest:02x}".encode("ascii") + b"]"


@functools.cache
def _discovery_pattern(
    staff_layout: StaffLayout, contract_layout: ContractLayout, team_lists: TeamListLayout
) -> re.Pattern[bytes]:
    """The filtered pass's pattern: the chain tag, then a selector and a team id in range.

    A person id is far below the third byte of its word and a team id below the third byte of
    its own, so four of the eight bytes after the tag are bounded, which is what makes one pass
    over the section cheap enough to make at all. The bounds come from the layouts, so a wider
    id space means a wider class rather than a missed record.

    Raises:
        ValueError: The selector or team bound does not fit in three bytes, so the byte class
            its top byte needs cannot be built.
    """
    selector_maximum = staff_layout.discovery_selector_maximum
    team_maximum = team_lists.team_id_range[1]
    bounds = (
        (selector_maximum, "discovery_selector_maximum"),
        (team_maximum, "the top of team_id_range"),
    )
    for bound, bound_name in bounds:
        if not 0 <= bound >> 16 <= 0xFF:
            raise ValueError(f"{bound_name} ({bound}) must fit in three bytes")
    selector_offset = contract_layout.selector_offset
    team_offset = contract_layout.team_id_offset
    if team_offset != selector_offset + _UINT32.size:
        raise ValueError(
            f"the team id must follow the selector: team_id_offset ({team_offset}) must be "
            f"selector_offset ({selector_offset}) plus {_UINT32.size}"
        )
    tag = contract_layout.tag
    lead_bytes = selector_offset - len(tag)
    if lead_bytes < 0:
        raise ValueError(
            f"selector_offset ({selector_offset}) must leave room for the tag ({len(tag)} bytes)"
        )
    pattern = (
        re.escape(tag)
        + b"." * lead_bytes
        + b".."
        + _byte_class(selector_maximum >> 16)
        + b"\\x00"
        + b".."
        + _byte_class(team_maximum >> 16)
        + b"\\x00"
    )
    return re.compile(pattern, re.DOTALL)


@dataclass(frozen=True, slots=True)
class _Discovery:
    """What the filtered pass over `game_db` found, and what it counted.

    `records_by_person` holds each person's own contract records as (tag offset, record), in
    file order, and `header_by_person` the header the search behind each person's first record
    found. The headers come out of the same search the counts do, so they are returned with
    them rather than searched for a second time.
    """

    records_by_person: dict[int, list[tuple[int, ChainRecordTuple]]]
    header_by_person: dict[int, int]
    hits: int
    untailed_hits: int
    club_record_hits: int
    unowned_tailed_hits: int
    owned_records: int
    non_staff_tailed_hits: int


def discover_contracts(
    game_db: bytes,
    player_records: PlayerRecords,
    human_selector: int | None,
    decoder: ContractDecoder,
    layouts: StaffLayouts,
    club_index: ClubIndex,
) -> _Discovery:
    """Every contract record a person who is not a player owns, from one filtered pass.

    A record belongs to a person only when its tail parses and his own header sits in front of
    it. A hit with no tail is what a selector's four bytes look like where they are not a
    record at all, and no person owns one; a tailed hit whose header search fails belongs to
    somebody whose object is not a staff object, and is counted so that the checks can see it.
    Candidates inside closed club records are counted separately, since those bytes cannot
    be a standalone person object. Records whose selector is a player's or the human manager's
    are left to their own readers.
    """
    pattern = _discovery_pattern(layouts.staff, layouts.contracts, layouts.team_lists)
    selector_offset = layouts.contracts.selector_offset
    staff_layout = layouts.staff
    pindex_positions = player_records.position_by_pindex
    unpack_selector = _UINT32.unpack_from
    decode_chain_record = decoder.decode_chain_record
    records_by_person: dict[int, list[tuple[int, ChainRecordTuple]]] = {}
    header_by_person: dict[int, int] = {}
    hits = 0
    untailed_hits = 0
    club_record_hits = 0
    unowned_tailed_hits = 0
    owned_records = 0
    non_staff_tailed_hits = 0
    # A next accepted club header closes each of these spans. The final span ends at a
    # scan margin rather than a known closing header, so it must remain searchable.
    closed_clubs = club_index.record_spans[:-1]
    club_position = 0
    for match in pattern.finditer(game_db):
        tag_offset = match.start()
        hits += 1
        while (
            club_position < len(closed_clubs)
            and closed_clubs[club_position].record_end <= tag_offset
        ):
            club_position += 1
        if (
            club_position < len(closed_clubs)
            and closed_clubs[club_position].record_start <= tag_offset
        ):
            club_record_hits += 1
            continue
        selector: int = unpack_selector(game_db, tag_offset + selector_offset)[0]
        if selector == 0 or selector == human_selector:
            continue
        person_id = selector - _ID_OFFSET
        if person_id in pindex_positions:
            continue
        record = decode_chain_record(game_db, tag_offset)
        if not record[CHAIN_RECORD_HAS_TERMS]:
            untailed_hits += 1
            continue
        own_records = records_by_person.get(person_id)
        if own_records is None:
            header = locate_contracted_header(game_db, person_id, tag_offset, staff_layout)
            if header is None:
                if (
                    staff_layout.non_staff_contract_kinds
                    and _contract_header_with_kind(
                        game_db,
                        person_id,
                        tag_offset,
                        staff_layout,
                        staff_layout.non_staff_contract_kinds,
                    )
                    is not None
                ):
                    non_staff_tailed_hits += 1
                    continue
                unowned_tailed_hits += 1
                continue
            header_by_person[person_id] = header
            own_records = records_by_person[person_id] = []
        own_records.append((tag_offset, record))
        owned_records += 1
    return _Discovery(
        records_by_person=records_by_person,
        header_by_person=header_by_person,
        hits=hits,
        untailed_hits=untailed_hits,
        club_record_hits=club_record_hits,
        unowned_tailed_hits=unowned_tailed_hits,
        owned_records=owned_records,
        non_staff_tailed_hits=non_staff_tailed_hits,
    )


def _latest_started(
    records: Sequence[tuple[int, ChainRecordTuple]],
) -> tuple[int, ChainRecordTuple]:
    """The record of a person at one club that is the one in effect: the latest to start.

    Every own record measured has started and has not ended, so the latest start is the one he
    is really on; a tie goes to the one stored first.
    """

    def sort_key(entry: tuple[int, ChainRecordTuple]) -> tuple[date, int]:
        start = entry[1][CHAIN_RECORD_START]
        return (_UNDATED_START if start is None else start, -entry[0])

    return max(records, key=sort_key)


def _human_records(
    game_db: bytes,
    header: int,
    object_end: int,
    selector: int,
    decoder: ContractDecoder,
    layouts: StaffLayouts,
) -> list[tuple[int, ChainRecordTuple]]:
    """The human manager's own contract records, from inside his own object.

    His object runs to megabytes and his one record sits a few hundred bytes before its end, so
    his selector is looked for over the whole object rather than in any window of the layout's.
    """
    tag = layouts.contracts.tag
    selector_offset = layouts.contracts.selector_offset
    needle = _UINT32.pack(selector)
    find = game_db.find
    startswith = game_db.startswith
    records: list[tuple[int, ChainRecordTuple]] = []
    hit = find(needle, header, object_end)
    while hit >= 0:
        tag_offset = hit - selector_offset
        if tag_offset >= header and startswith(tag, tag_offset):
            record = decoder.decode_chain_record(game_db, tag_offset)
            if record[CHAIN_RECORD_HAS_TERMS]:
                records.append((tag_offset, record))
        hit = find(needle, hit + 1, object_end)
    return records


@dataclass(frozen=True, slots=True)
class _AbilityBlock:
    """What one staff object's ability block holds, once its signature has read."""

    ability: Ability
    preferences: StaffPreferences
    unknown: Mapping[str, int]


def _read_ability_block(
    game_db: bytes, header: int, layout: StaffLayout
) -> tuple[_AbilityBlock | None, bool, bool, bool]:
    """(block, preference slots in range, codes in set, further bytes in range).

    The block sits a fixed distance past the entry list, whose length the header stores, and it
    is read only when both abilities are inside `ability_range` and the sentinel byte holds its
    one value. Without that the position is not to be trusted, so nothing read from it ships,
    and the three shares below are counted as failures.

    A header near the end of the section has no room for an object, and the entry count is the
    first byte past what the header test itself reads, so its own place is checked before it is
    read. Such a header is the no-block case, exactly as a block running past the section is.
    """
    section_end = len(game_db)
    entry_count_offset = header + layout.entry_count_offset
    if entry_count_offset < 0 or entry_count_offset >= section_end:
        return None, False, False, False
    entry_count = game_db[entry_count_offset]
    ability_at = header + layout.ability_base_offset + layout.entry_bytes * entry_count
    block_end = ability_at + layout.block_40_offset + layout.block_40_count
    if ability_at < 0 or block_end > section_end:
        return None, False, False, False
    lowest_ability, highest_ability = layout.ability_range
    current: int = _UINT16.unpack_from(game_db, ability_at + layout.current_ability_offset)[0]
    potential: int = _INT16.unpack_from(game_db, ability_at + layout.potential_ability_offset)[0]
    sentinel = game_db[ability_at + layout.sentinel_offset]
    preferences_at = ability_at + layout.preferences_offset
    preferences = game_db[preferences_at : preferences_at + layout.preference_count]
    lowest_preference, highest_preference = layout.preference_range
    slots_in_range = all(
        lowest_preference <= preferences[slot] <= highest_preference
        or (slot, preferences[slot]) in layout.preference_slot_sentinels
        for slot in layout.range_checked_preference_slots
    )
    codes_at = ability_at + layout.codes_offset
    codes = game_db[codes_at : codes_at + layout.code_count]
    codes_in_set = all(code in layout.code_set for code in codes)
    further_at = ability_at + layout.block_40_offset
    lowest_further, highest_further = layout.block_40_range
    further_in_range = all(
        lowest_further <= value <= highest_further for value in game_db[further_at:block_end]
    )
    if not (
        lowest_ability <= current <= highest_ability
        and lowest_ability <= potential <= highest_ability
        and sentinel == layout.sentinel_value
    ):
        return None, slots_in_range, codes_in_set, further_in_range
    unknown: dict[str, int] = {
        _ENTRY_COUNT_KEY: entry_count,
        _ROLE_KEY: game_db[ability_at + layout.r4_offset],
    }
    for code_number, code in enumerate(codes, start=layout.codes_offset):
        unknown[f"r{code_number}"] = code
    for slot in layout.unnamed_preference_slots:
        unknown[f"preference_slot_{slot}"] = preferences[slot]
    for b40_idx, b40_val in enumerate(game_db[further_at:block_end]):
        unknown[f"b40_raw_{b40_idx}"] = b40_val
        unknown[f"b40_20_{b40_idx}"] = max(1, min(20, (b40_val + 2) // 5))
    block = _AbilityBlock(
        ability=Ability(current=current, potential=potential, potential_range_code=None),
        preferences=StaffPreferences(
            *(preferences[slot] for _name, slot in layout.named_preference_slots)
        ),
        unknown=unknown,
    )
    return block, slots_in_range, codes_in_set, further_in_range


@dataclass(frozen=True, slots=True)
class _PersonObject:
    """One person's object, decoded once however many clubs give him a row."""

    header: int
    uid: int
    unique_id: int | None
    is_human_manager: bool
    person: PersonTuple | None
    block: _AbilityBlock | None


def _next_header_after(headers: Sequence[int], header: int) -> int | None:
    """The nearest known header after `header`, or None when it is the last one known."""
    position = bisect_left(headers, header + 1)
    return headers[position] if position < len(headers) else None


def _unique_id(
    game_db: bytes,
    person_id: int,
    header: int,
    uid: int,
    next_header: int | None,
    layout: StaffLayout,
) -> int | None:
    """A person's database Unique ID, from the header that closes his object, or None.

    That header lies after his own and no further on than the next header the decode knows
    of, which may be it; the next header's uid is the highest the closing one can carry.
    """
    search_start = header + layout.kind_offset + 1
    if next_header is None:
        search_end = len(game_db)
        uid_ceiling = None
    else:
        search_end = next_header + _UINT32.size
        next_values = _header_values(game_db, next_header, _header_reader(layout), layout)
        uid_ceiling = None if next_values is None else next_values[0]
    return closing_unique_id(game_db, person_id, search_start, search_end, uid, uid_ceiling)


def _person_block_window(
    game_db: bytes,
    header: int,
    tag_offset: int | None,
    next_header: int | None,
    layout: StaffLayout,
) -> tuple[int, int]:
    """[start, end) to look for one person's name block in.

    A contracted person's block follows his own contract record, at most 1,534 bytes past the
    tag on the saves measured, so the search starts just past the record and runs for
    `person_block_search_bytes`. A person with no record has his block in front of whatever
    follows his header instead. Either way the window stops at the next header, so one
    person's block is never read as another's.
    """
    section_end = len(game_db)
    if tag_offset is None:
        start = header + layout.kind_offset
        end = header + layout.list_only_block_search_bytes
    else:
        start = tag_offset + layout.person_block_offset_after_tag
        end = tag_offset + layout.person_block_search_bytes
    if next_header is not None:
        end = min(end, next_header)
    end = min(end, section_end)
    return start, max(end, start)


def _staff_unknown(
    object_unknown: Mapping[str, int] | None, record: ChainRecordTuple | None
) -> FrozenMapping[str, int]:
    """One row's unknown map: the object's keys, then the contract's.

    A key is left out rather than stored empty, so a person whose ability block does not read
    carries none of its keys and a person with no contract none of the contract's.
    """
    unknown: dict[str, int] = {} if object_unknown is None else dict(object_unknown)
    if record is not None:
        status = record[CHAIN_RECORD_SQUAD_STATUS]
        if status is not None:
            unknown[_CONTRACT_STATUS_KEY] = status
        tail_unknown = record[CHAIN_RECORD_UNKNOWN]
        if tail_unknown is not None:
            for key, tail_key in _CONTRACT_TAIL_KEYS:
                tail_value = tail_unknown.get(tail_key)
                if tail_value is not None:
                    unknown[key] = tail_value
        contract_type = record[CHAIN_RECORD_CONTRACT_TYPE]
        if contract_type is not None:
            unknown[_CONTRACT_TYPE_KEY] = contract_type
    return FrozenMapping(unknown)


def _team_slot(club_index: ClubIndex, team_id: int | None) -> int | None:
    """The slot a team holds in the list of the club that fields it, or None."""
    if team_id is None:
        return None
    claiming_club = club_index.team_to_club.get(team_id)
    if claiming_club is None:
        claiming_club = club_index.affiliate_team_to_club.get(team_id)
    return None if claiming_club is None else claiming_club[1]


def read_staff(
    game_db: bytes,
    humans: bytes,
    club_index: ClubIndex,
    player_records: PlayerRecords,
    name_pools: NamePools,
    clock: date,
    layouts: StaffLayouts,
    file_name: str,
) -> tuple[tuple[Staff, ...], tuple[StaffList, ...], StaffStats]:
    """Every club's staff and every club's staff lists, with what the pass counted.

    Staff rows come in the order the people's objects sit in the section, and a person several
    clubs employ comes once per club, by club uid. List rows come in club index order, three
    per club that lists at least one person who is not a player.

    Raises:
        CorruptSaveError: A contract record's team id or wage runs past the end of the section,
            or a name block's relation list runs past the window it was found in.
    """
    staff_layout = layouts.staff
    contract_decoder = build_contract_decoder(layouts.contracts, club_index, clock, file_name)
    person_decoder = build_person_block_decoder(
        layouts.person_blocks, name_pools, club_index, clock, file_name
    )
    human_selector = first_human_selector(humans, layouts.humans, file_name)

    listed_pairs, lists_by_club, list_counts = read_staff_lists(
        game_db, club_index, player_records, staff_layout
    )
    discovery = discover_contracts(
        game_db, player_records, human_selector, contract_decoder, layouts, club_index
    )

    header_by_person = dict(discovery.header_by_person)
    listed_persons = sorted({person_id for _club_uid, person_id in listed_pairs})
    ambiguous_headers = 0
    unlocated_persons = 0
    for person_id in listed_persons:
        if person_id in header_by_person:
            continue
        located = locate_listed_header(game_db, person_id, player_records, staff_layout)
        if located is _AMBIGUOUS:
            ambiguous_headers += 1
        elif located is None:
            unlocated_persons += 1
        else:
            header_by_person[person_id] = cast("int", located)

    human_person_id: int | None = None
    if human_selector is not None:
        human_header = locate_human_header(game_db, human_selector, staff_layout)
        if human_header is not None:
            human_person_id = human_selector - _ID_OFFSET
            header_by_person[human_person_id] = human_header

    # Every header the decode knows of, so a name-block window can stop at the next one.
    player_header_offset = player_records.layout.pindex_offset
    boundaries = sorted(
        {record_offset + player_header_offset for record_offset in player_records.record_offsets}
        | set(header_by_person.values())
    )

    records_by_person = discovery.records_by_person
    if human_person_id is not None:
        human_header = header_by_person[human_person_id]
        object_end = _next_header_after(boundaries, human_header) or len(game_db)
        found_records = _human_records(
            game_db,
            human_header,
            object_end,
            cast("int", human_selector),
            contract_decoder,
            layouts,
        )
        if found_records:
            records_by_person[human_person_id] = found_records
        else:
            del header_by_person[human_person_id]
            human_person_id = None

    rows_by_club_and_person, membership = _merge_membership(
        listed_pairs, records_by_person, header_by_person, club_index
    )
    if human_person_id is not None:
        human_record = _latest_started(records_by_person[human_person_id])
        human_club_uid = human_record[1][CHAIN_RECORD_CLUB_UID]
        if human_club_uid is None:
            del header_by_person[human_person_id]
            human_person_id = None
        else:
            rows_by_club_and_person[(human_club_uid, human_person_id)] = (human_record, (), None)

    row_persons = {person_id for _club_uid, person_id in rows_by_club_and_person}
    objects: dict[int, _PersonObject] = {}
    staff_objects = 0
    ability_signatures = 0
    preference_slots_in_range = 0
    codes_in_set = 0
    block_40_in_range = 0
    persons_with_block = 0
    for person_id in sorted(row_persons):
        header = header_by_person[person_id]
        header_values = _header_values(game_db, header, _header_reader(staff_layout), staff_layout)
        # Every header here passed the same test when it was located.
        uid, kind = cast("tuple[int, int]", header_values)
        is_human_manager = kind == staff_layout.human_kind
        block: _AbilityBlock | None = None
        if not is_human_manager:
            staff_objects += 1
            block, slots_ok, codes_ok, further_ok = _read_ability_block(
                game_db, header, staff_layout
            )
            if block is not None:
                ability_signatures += 1
            preference_slots_in_range += int(slots_ok)
            codes_in_set += int(codes_ok)
            block_40_in_range += int(further_ok)
        next_header = _next_header_after(boundaries, header)
        unique_id = _unique_id(game_db, person_id, header, uid, next_header, staff_layout)
        own_records = records_by_person.get(person_id)
        tag_offset = None if own_records is None else _latest_started(own_records)[0]
        window_start, window_end = _person_block_window(
            game_db, header, tag_offset, next_header, staff_layout
        )
        person = person_decoder.decode(game_db, window_start, window_end)
        if person is not None:
            persons_with_block += 1
        objects[person_id] = _PersonObject(
            header=header,
            uid=uid,
            unique_id=unique_id,
            is_human_manager=is_human_manager,
            person=person,
            block=block,
        )

    rows = _build_rows(rows_by_club_and_person, objects, club_index)
    list_rows = _build_list_rows(lists_by_club, objects, club_index)
    listed_persons_staff = sum(
        1
        for person_id in listed_persons
        if (person_object := objects.get(person_id)) is not None
        and not person_object.is_human_manager
        and person_object.person is not None
    )
    stats = StaffStats(
        clubs_checked=list_counts.clubs_checked,
        clubs_lists_fit=list_counts.clubs_lists_fit,
        list_values=list_counts.list_values,
        player_values_in_lists=list_counts.player_values_in_lists,
        unset_list_values=list_counts.unset_list_values,
        listed_persons=len(listed_persons),
        listed_persons_staff=listed_persons_staff,
        staff_objects=staff_objects,
        ability_signatures=ability_signatures,
        preference_slots_in_range=preference_slots_in_range,
        codes_in_set=codes_in_set,
        block_40_in_range=block_40_in_range,
        persons=len(row_persons),
        persons_with_block=persons_with_block,
        discovery_hits=discovery.hits,
        untailed_hits=discovery.untailed_hits,
        club_record_hits=discovery.club_record_hits,
        unowned_tailed_hits=discovery.unowned_tailed_hits,
        owned_records=discovery.owned_records,
        listed_pairs=len(listed_pairs),
        listed_pairs_contracted_here=membership.listed_pairs_contracted_here,
        merged_affiliate_pairs=membership.merged_affiliate_pairs,
        ambiguous_headers=ambiguous_headers,
        unlocated_persons=unlocated_persons,
        unresolved_contract_teams=membership.unresolved_contract_teams,
        repeat_contracts=membership.repeat_contracts,
        human_found=human_person_id is not None,
        rows=len(rows),
        list_rows=len(list_rows),
        non_staff_tailed_hits=discovery.non_staff_tailed_hits,
    )
    return rows, list_rows, stats


@dataclass(frozen=True, slots=True)
class _MembershipCounts:
    """What merging the listed and the contracted people counted."""

    listed_pairs_contracted_here: int
    merged_affiliate_pairs: int
    unresolved_contract_teams: int
    repeat_contracts: int


# One row before its record is built: its contract record, the list numbers holding the person
# and the club whose own list holds him, which is the row's club unless an affiliate side of it
# listed him.
type _RowSource = tuple[tuple[int, ChainRecordTuple] | None, tuple[int, ...], int | None]


def _merge_membership(
    listed_pairs: Mapping[tuple[int, int], tuple[int, ...]],
    records_by_person: Mapping[int, list[tuple[int, ChainRecordTuple]]],
    header_by_person: Mapping[int, int],
    club_index: ClubIndex,
) -> tuple[dict[tuple[int, int], _RowSource], _MembershipCounts]:
    """The (club, person) rows to build, each with its contract record and its list numbers.

    A person a club both lists and pays is one row. A person an affiliate side lists whose
    contract is at that side's parent belongs to the parent, keeping the side that listed him
    and its list numbers; any other listing stands on its own at the club that made it. A
    person nobody lists is a row wherever his contract is.

    One case the saves measured hold none of: a person listed by **both** an affiliate side and
    its parent would be one row either way, and the two listings would write the same key here,
    so whichever club's record comes last keeps its own list numbers and the other's are lost.
    Nothing is restructured for a pair no save has; it is written down so that a save that does
    have one is read as a known gap rather than a surprise.
    """
    contracted: dict[tuple[int, int], tuple[int, ChainRecordTuple]] = {}
    clubs_by_person: dict[int, set[int]] = {}
    unresolved_contract_teams = 0
    repeat_contracts = 0
    for person_id, own_records in records_by_person.items():
        if person_id not in header_by_person:
            continue
        records_by_club: dict[int, list[tuple[int, ChainRecordTuple]]] = {}
        for entry in own_records:
            club_uid = entry[1][CHAIN_RECORD_CLUB_UID]
            if club_uid is None:
                unresolved_contract_teams += 1
                continue
            records_by_club.setdefault(club_uid, []).append(entry)
        for club_uid, club_records in records_by_club.items():
            if len(club_records) > 1:
                repeat_contracts += 1
            contracted[(club_uid, person_id)] = _latest_started(club_records)
            clubs_by_person.setdefault(person_id, set()).add(club_uid)

    parent_by_club_uid = {
        club.uid: club.parent_club_uid
        for club in club_index.clubs
        if club.parent_club_uid is not None
    }
    rows: dict[tuple[int, int], _RowSource] = {}
    listed_pairs_contracted_here = 0
    merged_affiliate_pairs = 0
    for (club_uid, person_id), list_numbers in listed_pairs.items():
        if person_id not in header_by_person:
            continue
        own_record = contracted.get((club_uid, person_id))
        if own_record is not None:
            listed_pairs_contracted_here += 1
            rows[(club_uid, person_id)] = (own_record, list_numbers, club_uid)
            continue
        parent_club_uid = parent_by_club_uid.get(club_uid)
        contract_clubs = clubs_by_person.get(person_id)
        if (
            parent_club_uid is not None
            and contract_clubs is not None
            and parent_club_uid in contract_clubs
        ):
            listed_pairs_contracted_here += 1
            merged_affiliate_pairs += 1
            rows[(parent_club_uid, person_id)] = (
                contracted[(parent_club_uid, person_id)],
                list_numbers,
                club_uid,
            )
            continue
        rows[(club_uid, person_id)] = (None, list_numbers, club_uid)
    for key, own_record in contracted.items():
        if key not in rows:
            rows[key] = (own_record, (), None)
    return rows, _MembershipCounts(
        listed_pairs_contracted_here=listed_pairs_contracted_here,
        merged_affiliate_pairs=merged_affiliate_pairs,
        unresolved_contract_teams=unresolved_contract_teams,
        repeat_contracts=repeat_contracts,
    )


def _build_rows(
    rows_by_club_and_person: Mapping[tuple[int, int], _RowSource],
    objects: Mapping[int, _PersonObject],
    club_index: ClubIndex,
) -> tuple[Staff, ...]:
    """One `Staff` per row, ordered by where the person's object sits and then by club uid."""
    rows: list[Staff] = []
    ordered_keys = sorted(rows_by_club_and_person, key=lambda key: (objects[key[1]].header, key[0]))
    for key in ordered_keys:
        club_uid, person_id = key
        own_record, list_numbers, listed_club_uid = rows_by_club_and_person[key]
        person_object = objects[person_id]
        person = person_object.person
        block = person_object.block
        club = club_index.club_by_uid.get(club_uid)
        listed_club = (
            None if listed_club_uid is None else club_index.club_by_uid.get(listed_club_uid)
        )
        record = None if own_record is None else own_record[1]
        team_id = None if record is None else record[CHAIN_RECORD_TEAM_ID]
        personality = None if person is None else person[_PERSON_PERSONALITY]
        rows.append(
            Staff(
                uid=person_object.uid,
                unique_id=person_object.unique_id,
                is_human_manager=person_object.is_human_manager,
                name=None if person is None else person[_PERSON_NAME],
                first_name=None if person is None else person[_PERSON_FIRST_NAME],
                last_name=None if person is None else person[_PERSON_LAST_NAME],
                common_name=None if person is None else person[_PERSON_COMMON_NAME],
                full_name=None if person is None else person[_PERSON_FULL_NAME],
                legal_name=None if person is None else person[_PERSON_LEGAL_NAME],
                birth_date=None if person is None else person[_PERSON_BIRTH_DATE],
                age=None if person is None else person[_PERSON_AGE],
                nation_id=None if person is None else person[_PERSON_NATION_ID],
                club_uid=club_uid,
                club_name="" if club is None else club.name,
                team_id=team_id,
                team_slot=_team_slot(club_index, team_id),
                listed_club_uid=listed_club_uid,
                listed_club_name=None if listed_club is None else listed_club.name,
                in_club_lists=bool(list_numbers),
                list_indexes=list_numbers,
                has_contract=record is not None,
                wage=None if record is None else record[CHAIN_RECORD_WAGE],
                contract_start=None if record is None else record[CHAIN_RECORD_START],
                contract_end=None if record is None else record[CHAIN_RECORD_END],
                ability=None if block is None else block.ability,
                personality=personality,
                attributes=(
                    None if personality is None else StaffAttributes(personality.adaptability)
                ),
                preferences=None if block is None else block.preferences,
                unknown=_staff_unknown(None if block is None else block.unknown, record),
            )
        )
    return tuple(rows)


def _build_list_rows(
    lists_by_club: Mapping[int, tuple[tuple[int, ...], ...]],
    objects: Mapping[int, _PersonObject],
    club_index: ClubIndex,
) -> tuple[StaffList, ...]:
    """Three rows per club that lists somebody, in club index order.

    A club whose lists name nobody but players, or nobody at all, has no row here. A person
    whose object could not be told from another's has no uid to give and is left out of the
    list he is named in, exactly as he is left out of `staff()`.
    """
    rows: list[StaffList] = []
    for club in club_index.clubs:
        club_lists = lists_by_club.get(club.uid)
        if club_lists is None or not any(club_lists):
            continue
        for list_index, person_ids in enumerate(club_lists):
            known = [objects[person_id] for person_id in person_ids if person_id in objects]
            rows.append(
                StaffList(
                    club_uid=club.uid,
                    club_name=club.name,
                    list_index=list_index,
                    staff_uids=tuple(person_object.uid for person_object in known),
                    staff_names=tuple(
                        None if person_object.person is None else person_object.person[_PERSON_NAME]
                        for person_object in known
                    ),
                )
            )
    return tuple(rows)
