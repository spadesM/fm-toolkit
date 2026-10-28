"""Reading the clubs run by the save's human managers.

The `humans` section names the first human manager by a selector: the manager's person id
plus 1. Two independent routes link that manager to a club:

- Route 1 finds the contract chain records in `game_db` that carry the selector, decodes each
  with `ContractDecoder.decode_chain_record`, and takes the club of the best record whose team
  resolves to a club and whose contract has not ended before the in-game date: one with a
  parsed tail first, then the latest end.
- Route 2 looks through the strings of `save_game_summary` for a club short name directly
  followed by that club's uid. The string that ends exactly where it starts is the manager
  name.

Route 1 is the primary answer and route 2 checks it. When neither route finds a club, for
example while the manager is between jobs, no managed club is listed. The manager's person uid
comes from the single person header in `game_db` that stores the person id followed by a
doubled uid.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

from fm26save._core._container import damaged_part_error
from fm26save._core._errors import CorruptSaveError
from fm26save._core._layouts import ContractLayout, HumansLayout, SummaryStringsLayout, find_layout
from fm26save._core._reader_stats import ManagedStats
from fm26save._core._scan import read_u16, read_u32
from fm26save._core.models.clubs import Club
from fm26save._core.models.managed import ManagedClub
from fm26save._core.readers._common import (
    GAME_DB_SECTION,
    HUMANS_SECTION,
    MISSING_REFERENCE,
    SAVE_SUMMARY_SECTION,
    build_gap_padded_struct,
    layout_mismatch,
)
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.contracts import (
    CHAIN_RECORD_CLUB_UID,
    CHAIN_RECORD_END,
    CHAIN_RECORD_HAS_TERMS,
    build_contract_decoder,
)

_U32 = struct.Struct("<I")
_U32_BYTES = _U32.size
_NO_PERSON_UIDS = frozenset({0, MISSING_REFERENCE})


@dataclass(frozen=True, slots=True)
class ManagedClubLayouts:
    """The layouts the managed-club reader uses."""

    humans: HumansLayout
    summary_strings: SummaryStringsLayout
    contracts: ContractLayout


def find_managed_club_layouts(section_schemas: Mapping[str, int], build: str) -> ManagedClubLayouts:
    """Look up the managed-club layouts for the save's section schemas, falling back to the build."""
    return ManagedClubLayouts(
        humans=find_layout(
            HumansLayout, HUMANS_SECTION, section_schemas.get(HUMANS_SECTION), build
        ).layout,
        summary_strings=find_layout(
            SummaryStringsLayout,
            SAVE_SUMMARY_SECTION,
            section_schemas.get(SAVE_SUMMARY_SECTION),
            build,
        ).layout,
        contracts=find_layout(
            ContractLayout, GAME_DB_SECTION, section_schemas.get(GAME_DB_SECTION), build
        ).layout,
    )


class _SummaryString(NamedTuple):
    """One string found in `save_game_summary`: where its length word starts and its text ends."""

    length_offset: int
    end_offset: int
    text: str


def _scan_summary_strings(summary: bytes, layout: SummaryStringsLayout) -> list[_SummaryString]:
    """Every non-overlapping length-prefixed string, in file order (see SummaryStringsLayout)."""
    shortest_length, longest_length = layout.string_length_range
    lowest_character = chr(layout.lowest_code_point)
    summary_length = len(summary)
    last_length_offset = summary_length - _U32_BYTES
    unpack_length = _U32.unpack_from
    found_strings: list[_SummaryString] = []
    offset = max(layout.strings_start_offset, 0)
    while offset <= last_length_offset:
        text_length: int = unpack_length(summary, offset)[0]
        text_start = offset + _U32_BYTES
        text_end = text_start + text_length
        if shortest_length <= text_length <= longest_length and text_end <= summary_length:
            try:
                text = summary[text_start:text_end].decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None and min(text) >= lowest_character:
                found_strings.append(_SummaryString(offset, text_end, text))
                offset = text_end
                continue
        offset += 1
    return found_strings


def read_summary_strings(summary: bytes, layout: SummaryStringsLayout) -> tuple[str, ...]:
    """The readable strings of a `save_game_summary` section, in file order.

    Never raises: bytes that do not form a string are skipped.
    """
    return tuple(found_string.text for found_string in _scan_summary_strings(summary, layout))


class _SummaryLink(NamedTuple):
    """A club short name in the summary followed by its club's uid, and the adjacent name."""

    club: Club
    manager_name: str | None


def _summary_links(
    summary: bytes, layout: SummaryStringsLayout, club_index: ClubIndex
) -> list[_SummaryLink]:
    """Route 2: every summary string that is followed by the uid of a club with that short name."""
    summary_length = len(summary)
    club_by_uid = club_index.club_by_uid
    links: list[_SummaryLink] = []
    previous_string: _SummaryString | None = None
    for found_string in _scan_summary_strings(summary, layout):
        uid_offset = found_string.end_offset
        if uid_offset + _U32_BYTES <= summary_length:
            club = club_by_uid.get(_U32.unpack_from(summary, uid_offset)[0])
            if club is not None and club.short_name == found_string.text:
                manager_name = (
                    previous_string.text
                    if previous_string is not None
                    and previous_string.end_offset == found_string.length_offset
                    else None
                )
                links.append(_SummaryLink(club, manager_name))
        previous_string = found_string
    return links


def _chain_record_club(
    game_db: bytes,
    selector: int,
    club_index: ClubIndex,
    clock: date,
    layout: ContractLayout,
    file_name: str,
) -> Club | None:
    """Route 1: the club of the best chain record carrying `selector`, or None.

    A hit of the selector counts only when the contract tag sits `selector_offset` bytes before
    it. Records whose team resolves to no club, and records whose end date is before `clock`,
    are skipped; a record without a parsed tail or with no end date is kept. Of the rest, a
    record with a parsed tail beats one without, then a later end beats an earlier or missing
    one, and the first in file order wins a tie.

    Raises:
        CorruptSaveError: A matching chain record runs past the end of game_db.
    """
    decoder = build_contract_decoder(layout, club_index, clock, file_name)
    decode_chain_record = decoder.decode_chain_record
    club_by_uid = club_index.club_by_uid
    tag = layout.tag
    tag_distance = layout.selector_offset
    selector_bytes = _U32.pack(selector)
    find = game_db.find
    startswith = game_db.startswith
    best_club: Club | None = None
    best_rank: tuple[bool, date] | None = None
    hit = find(selector_bytes, tag_distance)
    while hit >= 0:
        chain_tag_offset = hit - tag_distance
        if startswith(tag, chain_tag_offset):
            chain_record = decode_chain_record(game_db, chain_tag_offset)
            club_uid = chain_record[CHAIN_RECORD_CLUB_UID]
            club = club_by_uid.get(club_uid) if club_uid is not None else None
            record_end = chain_record[CHAIN_RECORD_END]
            if club is not None and (record_end is None or record_end >= clock):
                rank = (chain_record[CHAIN_RECORD_HAS_TERMS], record_end or date.min)
                if best_rank is None or rank > best_rank:
                    best_club = club
                    best_rank = rank
        hit = find(selector_bytes, hit + 1)
    return best_club


def _manager_staff_uid(game_db: bytes, selector: int, layout: HumansLayout) -> int | None:
    """The uid of the only person header for person id `selector - 1`, or None.

    A header is the person id followed by a doubled uid that is neither 0 nor FFFFFFFF. No
    header, or more than one, gives None.

    Raises:
        ValueError: The layout's two uid fields overlap.
    """
    uid_struct, uid_struct_offset, _index_by_name = build_gap_padded_struct(
        [
            (layout.person_uid_offset, "I", "uid"),
            (layout.person_uid_copy_offset, "I", "uid_copy"),
        ]
    )
    unpack_uids = uid_struct.unpack_from
    last_header_offset = len(game_db) - uid_struct_offset - uid_struct.size
    person_id_bytes = _U32.pack(selector - 1)
    find = game_db.find
    found_uid: int | None = None
    hit = find(person_id_bytes)
    while 0 <= hit <= last_header_offset:
        person_uid, person_uid_copy = unpack_uids(game_db, hit + uid_struct_offset)
        if person_uid == person_uid_copy and person_uid not in _NO_PERSON_UIDS:
            if found_uid is not None:
                return None
            found_uid = person_uid
        hit = find(person_id_bytes, hit + 1)
    return found_uid


def _first_human(humans: bytes, layout: HumansLayout, file_name: str) -> tuple[int, int] | None:
    """(human count, first human manager's selector), or None when the save lists no human.

    Raises:
        CorruptSaveError: The section ends before the count or the selector.
    """
    try:
        human_count = read_u16(humans, layout.human_count_offset)
        if human_count == 0:
            return None
        return human_count, read_u32(humans, layout.first_selector_offset)
    except CorruptSaveError as error:
        raise damaged_part_error(file_name, f"section {HUMANS_SECTION!r}", error) from error


def first_human_selector(humans: bytes, layout: HumansLayout, file_name: str) -> int | None:
    """The first human manager's selector (person id plus 1), or None.

    None means the save lists no human manager, or stores no person id for him.

    Raises:
        CorruptSaveError: The `humans` section ends before the count or the selector.
    """
    first_human = _first_human(humans, layout, file_name)
    if first_human is None:
        return None
    _human_count, selector = first_human
    return None if selector in _NO_PERSON_UIDS else selector


class ManagedClubsResult(NamedTuple):
    """The managed-club rows, and what the reader found on the way for the checks."""

    managed_clubs: tuple[ManagedClub, ...]
    stats: ManagedStats


def resolve_managed_clubs(
    humans: bytes,
    game_db: bytes,
    summary: bytes,
    club_index: ClubIndex,
    clock: date,
    layouts: ManagedClubLayouts,
    file_name: str,
) -> ManagedClubsResult:
    """The club run by the save's first human manager, as a one-row tuple or (), with counts.

    Only the first human manager is read, even when the save counts more than one. The rows
    are () when the save lists no human manager, or when no managed club is found, for example
    while the manager is between jobs. The stats count the human managers, whether each route
    found a club, and the rows.

    With one human manager, the summary must not link the manager to any club other than the
    one route 1 finds. With several, it is enough that one summary link names that club.

    Raises:
        CorruptSaveError: The `humans` section ends before the human count or the selector, or
            a chain record carrying the selector runs past the end of game_db.
        ReaderCheckError: Route 1 finds a club and the summary links the manager to another
            club (to only other clubs, when the save counts several human managers); or,
            without route 1, the summary links the manager to more than one club.
        ValueError: The layouts are inconsistent.
    """
    first_human = _first_human(humans, layouts.humans, file_name)
    if first_human is None:
        return ManagedClubsResult((), ManagedStats(0, 0, 0, 0))
    human_count, selector = first_human
    has_person_id = selector not in _NO_PERSON_UIDS
    chain_club = (
        _chain_record_club(game_db, selector, club_index, clock, layouts.contracts, file_name)
        if has_person_id
        else None
    )
    links = _summary_links(summary, layouts.summary_strings, club_index)
    linked_club_uids = sorted({link.club.uid for link in links})
    route_one_resolved = 0 if chain_club is None else 1
    route_two_resolved = 1 if linked_club_uids else 0

    if chain_club is not None:
        agreeing_links = [link for link in links if link.club.uid == chain_club.uid]
        has_other_links = len(agreeing_links) < len(links)
        if has_other_links and (human_count == 1 or not agreeing_links):
            raise layout_mismatch(
                file_name,
                f"the first human manager's contract names club uid {chain_club.uid}, but the "
                f"save summary links the manager to club uid "
                f"{', '.join(str(club_uid) for club_uid in linked_club_uids)}",
                HUMANS_SECTION,
            )
        club = chain_club
        manager_name = agreeing_links[0].manager_name if agreeing_links else None
    elif len(linked_club_uids) == 1:
        club = links[0].club
        manager_name = links[0].manager_name
    elif linked_club_uids:
        raise layout_mismatch(
            file_name,
            f"no contract links the first human manager to a club, and the save summary links "
            f"the manager to {len(linked_club_uids)} clubs",
            HUMANS_SECTION,
        )
    else:
        return ManagedClubsResult(
            (), ManagedStats(human_count, route_one_resolved, route_two_resolved, 0)
        )

    manager_staff_uid = (
        _manager_staff_uid(game_db, selector, layouts.humans) if has_person_id else None
    )
    managed_club = ManagedClub(
        club_uid=club.uid,
        club_name=club.name,
        club_short_name=club.short_name,
        manager_name=manager_name,
        manager_staff_uid=manager_staff_uid,
    )
    return ManagedClubsResult(
        (managed_club,), ManagedStats(human_count, route_one_resolved, route_two_resolved, 1)
    )
