"""Locating unserved suspension entries in `game_db` and joining them to their players.

A suspension entry has a shared core and either a null or attached-match suffix (see
`SuspensionLayout`). `locate_suspensions` scans the player region, from just before the first
player record to the end of `game_db`, with a compiled regex that resumes one byte after every
match start, so signatures that overlap one another are all considered. It gives each entry to
its owning player by bisecting the sorted record offsets. The pattern, the field Struct, the
offsets and the bounds are derived from the layout once per layout, and checked for
consistency at that point, so the search loop never reads the layout.

The established standalone null-form search is retained. Attached forms additionally require
a complete prefix/u8-count parent whose children all frame within one player's window. The
attachment is validated structurally; its unidentified values add no public fields.

An entry stores one id and one scope code that says what the id is. The layout lists which
codes name a competition and which name a nation, and every row built here reads the id
through the scope that gives it, so a nation id never reaches a competition field and a
competition id never reaches a nation one. The two really do share numbers inside one save,
so this is what keeps a ban from being named after an unrelated competition.
"""

from __future__ import annotations

import functools
import re
import struct
from bisect import bisect_right
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import SuspensionLayout
from fm26save._core._reader_stats import SuspensionStats
from fm26save._core._scan import decode_date
from fm26save._core.models.players import Player
from fm26save._core.models.suspensions import PlayerSuspension, Suspension, SuspensionScope
from fm26save._core.readers._common import build_gap_padded_struct
from fm26save._core.readers.player_scan import PlayerRecords


@dataclass(frozen=True, slots=True)
class SuspensionEntry:
    """One kept suspension entry, before it is joined to its player.

    Attributes:
        scope: What the ban covers, as `scope_code` says.
        scope_code: The scope code exactly as the entry stores it.
        scope_id: The u16 the entry stores beside the code: a competition id in the stage id
            space when the scope is COMPETITION, a nation id when it is NATION, and a number
            of no known meaning when the scope is UNKNOWN.
        issued: The date the ban was issued.
        e7: The unidentified u16 exported as `unknown["e7"]`.
        competition_name: The name of `scope_id` when the scope is COMPETITION and a name map
            named it; None otherwise. `named_entries` fills it in, so an entry is unnamed
            until the competition index has been read.
    """

    scope: SuspensionScope
    scope_code: int
    scope_id: int
    issued: date
    e7: int
    competition_name: str | None = None

    @property
    def competition_id(self) -> int | None:
        """`scope_id` when the ban covers one competition, and None otherwise."""
        return self.scope_id if self.scope is SuspensionScope.COMPETITION else None

    @property
    def nation_id(self) -> int | None:
        """`scope_id` when the ban covers a whole nation, and None otherwise."""
        return self.scope_id if self.scope is SuspensionScope.NATION else None


@dataclass(frozen=True, slots=True)
class _SuspensionSearch:
    """Everything `locate_suspensions` needs from a `SuspensionLayout`, derived once.

    `pattern` matches the signature from its first byte, which sits `pattern_offset` bytes
    after the entry start. `fields_struct` unpacks from the entry start, and the `*_index`
    fields give each value's position in its result.
    """

    pattern: re.Pattern[bytes]
    pattern_offset: int
    fields_struct: struct.Struct
    e7_index: int
    scope_code_index: int
    scope_id_index: int
    issued_date_offset: int
    owner_back_offset: int
    scope_id_lower_bound: int
    scope_id_upper_bound: int
    scope_by_code: Mapping[int, SuspensionScope]


def _build_signature_pattern(
    signature: tuple[tuple[int, int], ...],
) -> tuple[re.Pattern[bytes], int, int]:
    """(pattern, first_signature_offset, signature_end) for the signature's `(offset, value)`
    pairs: each signature byte literally, with `.{gap}` for the bytes between them.

    Raises:
        ValueError: The signature is empty, an offset is before the entry start, or an offset
            appears more than once.
    """
    if not signature:
        raise ValueError("the suspension signature must not be empty")
    sorted_signature = sorted(signature)
    first_offset = sorted_signature[0][0]
    if first_offset < 0:
        raise ValueError(
            f"signature offset {first_offset} is before the entry start; signature offsets "
            "count from the entry start"
        )
    pattern_parts: list[bytes] = []
    cursor = first_offset
    for offset, value in sorted_signature:
        gap = offset - cursor
        if gap < 0:
            raise ValueError(f"signature offset {offset} appears more than once")
        if gap:
            pattern_parts.append(b".{%d}" % gap)
        pattern_parts.append(re.escape(bytes((value,))))
        cursor = offset + 1
    return re.compile(b"".join(pattern_parts), re.DOTALL), first_offset, cursor


@functools.cache
def _suspension_search(layout: SuspensionLayout) -> _SuspensionSearch:
    """The layout's compiled search, built on first use for each layout.

    Raises:
        ValueError: The signature is empty, has an offset before the entry start or an offset
            listed twice; two fields overlap or a field starts before the entry start; a field
            ends past the last signature byte, so a signature match would not guarantee it is
            readable; `scope_id_exclusive_range` leaves no id strictly between its bounds; or
            one scope code is listed as both the competition code and a nation code.
    """
    pattern, pattern_offset, signature_end = _build_signature_pattern(layout.signature)
    # The issued date stays in the Struct only so the build-time overlap and signature-span
    # checks cover its four bytes; its value is read and validated by decode_date, never from
    # the unpacked tuple.
    field_specs = [
        (layout.unknown_e7_offset, "H", "e7"),
        (layout.issued_date_offset, "I", "issued_date"),
        (layout.scope_code_offset, "B", "scope_code"),
        (layout.scope_id_offset, "H", "scope_id"),
    ]
    fields_struct, _start_offset, index_by_name = build_gap_padded_struct(
        field_specs, start_offset=0
    )
    for offset, format_code, field_name in field_specs:
        if offset + struct.calcsize(format_code) > signature_end:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the last signature byte "
                f"(offset {signature_end - 1}), so a signature match does not guarantee it is "
                "readable"
            )
    lower_bound, upper_bound = layout.scope_id_exclusive_range
    if upper_bound - lower_bound < 2:
        raise ValueError(
            f"scope_id_exclusive_range {layout.scope_id_exclusive_range} leaves no scope id "
            "strictly between its bounds"
        )
    if layout.competition_scope_code in layout.nation_scope_codes:
        raise ValueError(
            f"scope code {layout.competition_scope_code} is listed as both the competition "
            "code and a nation code, so it would name two id spaces at once"
        )
    scope_by_code = {layout.competition_scope_code: SuspensionScope.COMPETITION}
    for code in layout.nation_scope_codes:
        scope_by_code[code] = SuspensionScope.NATION
    return _SuspensionSearch(
        pattern=pattern,
        pattern_offset=pattern_offset,
        fields_struct=fields_struct,
        e7_index=index_by_name["e7"],
        scope_code_index=index_by_name["scope_code"],
        scope_id_index=index_by_name["scope_id"],
        issued_date_offset=layout.issued_date_offset,
        owner_back_offset=layout.owner_back_offset,
        scope_id_lower_bound=lower_bound,
        scope_id_upper_bound=upper_bound,
        scope_by_code=scope_by_code,
    )


def locate_suspensions(
    game_db: bytes, player_records: PlayerRecords, layout: SuspensionLayout
) -> Mapping[int, tuple[SuspensionEntry, ...]]:
    """Every kept suspension entry, keyed by the position of its owning player record.

    Positions index `player_records.record_offsets` and come in ascending order; each
    player's entries keep the order of their offsets. A player with no entry has no key.
    The scan starts `owner_back_offset` bytes before the first record (or at 0) and resumes
    one byte after every match start, kept or not, so a false signature cannot hide a real
    entry that overlaps it. An entry is kept when it has an owner, a valid issued date (a
    readable game date, so day 366 of a non-leap year is rejected) and a scope id strictly
    inside the layout's range. A scope code the layout does not list keeps its entry, with the
    scope UNKNOWN, so the ban is still reported: only the meaning of its id is withheld.
    Attached forms also require a complete counted parent, valid attachment dates and the
    layout's attachment markers. An incomplete parent adds no attached entries and does not
    discard standalone entries accepted by the established search.

    Raises:
        ValueError: The layout is inconsistent (see `_suspension_search`).
    """
    search = _suspension_search(layout)
    record_offsets = player_records.record_offsets
    if not record_offsets:
        return {}
    find_signature = search.pattern.search
    pattern_offset = search.pattern_offset
    owner_back_offset = search.owner_back_offset
    unpack_from = search.fields_struct.unpack_from
    e7_index = search.e7_index
    scope_code_index = search.scope_code_index
    scope_id_index = search.scope_id_index
    issued_date_offset = search.issued_date_offset
    lower_bound = search.scope_id_lower_bound
    upper_bound = search.scope_id_upper_bound
    scope_for_code = search.scope_by_code.get
    unknown_scope = SuspensionScope.UNKNOWN
    game_db_length = len(game_db)

    region_start = max(0, record_offsets[0] - owner_back_offset)
    entries_by_position: dict[int, list[tuple[int, SuspensionEntry]]] = {}
    match = find_signature(game_db, region_start, game_db_length)
    while match is not None:
        signature_start = match.start()
        match = find_signature(game_db, signature_start + 1, game_db_length)
        entry_offset = signature_start - pattern_offset
        if entry_offset < 0:
            continue
        position = bisect_right(record_offsets, entry_offset + owner_back_offset) - 1
        if position < 0:
            continue
        field_values = unpack_from(game_db, entry_offset)
        scope_id: int = field_values[scope_id_index]
        if not lower_bound < scope_id < upper_bound:
            continue
        issued = decode_date(game_db, entry_offset + issued_date_offset)
        if issued is None:
            continue
        scope_code: int = field_values[scope_code_index]
        entry = SuspensionEntry(
            scope_for_code(scope_code, unknown_scope),
            scope_code,
            scope_id,
            issued,
            field_values[e7_index],
        )
        position_entries = entries_by_position.get(position)
        if position_entries is None:
            entries_by_position[position] = [(entry_offset, entry)]
        else:
            position_entries.append((entry_offset, entry))
    attached_offsets: set[int] = set()
    for position, entry_offset, entry in _counted_attached_entries(
        game_db, player_records, layout, search
    ):
        if entry_offset in attached_offsets:
            continue
        attached_offsets.add(entry_offset)
        entries_by_position.setdefault(position, []).append((entry_offset, entry))
    return {
        position: tuple(entry for _, entry in sorted(entries, key=lambda item: item[0]))
        for position, entries in sorted(entries_by_position.items())
    }


@functools.cache
def _parent_search(
    layout: SuspensionLayout,
) -> tuple[re.Pattern[bytes], tuple[tuple[int, int], ...]]:
    """The counted-parent locator and the shared 18-byte entry constraints."""
    if not layout.parent_prefix or not layout.null_suffix:
        raise ValueError("suspension parent prefix and null suffix must not be empty")
    if layout.linked_entry_bytes <= layout.entry_core_bytes:
        raise ValueError("attached suspension entry must extend its common core")
    if not 0 <= layout.linked_date_offset <= layout.linked_entry_bytes - 4:
        raise ValueError("attached suspension date lies outside the entry")
    if not 0 <= layout.linked_flag_offset < layout.linked_entry_bytes:
        raise ValueError("attached suspension flag lies outside the entry")
    if any(not 0 <= offset < layout.linked_entry_bytes for offset, _ in layout.linked_signature):
        raise ValueError("attached suspension signature lies outside the entry")
    core_signature = tuple(
        (offset, value) for offset, value in layout.signature if offset < layout.entry_core_bytes
    )
    if layout.entry_core_bytes < _suspension_search(layout).fields_struct.size:
        raise ValueError("suspension fields extend beyond the common core")
    header_bytes = len(layout.parent_prefix) + 1
    constraints = tuple(enumerate(layout.parent_prefix)) + tuple(
        (header_bytes + offset, value) for offset, value in core_signature
    )
    pattern, _, _ = _build_signature_pattern(constraints)
    return pattern, core_signature


def _counted_attached_entries(
    game_db: bytes,
    player_records: PlayerRecords,
    layout: SuspensionLayout,
    search: _SuspensionSearch,
) -> Iterator[tuple[int, int, SuspensionEntry]]:
    """Add attached forms only after every child fits and decodes in one owned parent.

    The preceding prefix's meaning and the attachment's extra fields remain unconfirmed.
    A u8 count bounds the walk; no guessed match counts or namespace joins select framing.
    The older standalone signature search remains independent of this stricter path.
    """
    pattern, core_signature = _parent_search(layout)
    prefix_bytes = len(layout.parent_prefix)
    header_bytes = prefix_bytes + 1
    offsets = player_records.record_offsets
    match = pattern.search(game_db, max(0, offsets[0] - search.owner_back_offset))
    while match is not None:
        parent_at = match.start()
        # Invalid parents may overlap real ones, just as standalone signatures can.
        match = pattern.search(game_db, parent_at + 1)
        cursor = parent_at + header_bytes
        position = bisect_right(offsets, cursor + search.owner_back_offset) - 1
        if position < 0:
            continue
        end = (
            offsets[position + 1] - search.owner_back_offset
            if position + 1 < len(offsets)
            else len(game_db)
        )
        if parent_at < max(0, offsets[position] - search.owner_back_offset):
            continue
        count = game_db[parent_at + prefix_bytes]
        if not count:
            continue
        pending: list[tuple[int, int, SuspensionEntry]] = []
        for _ in range(count):
            if cursor + max(layout.entry_core_bytes, search.fields_struct.size) > end:
                break
            if any(game_db[cursor + offset] != value for offset, value in core_signature):
                break
            values = search.fields_struct.unpack_from(game_db, cursor)
            scope_id = values[search.scope_id_index]
            issued = decode_date(game_db, cursor + search.issued_date_offset)
            if (
                issued is None
                or not search.scope_id_lower_bound < scope_id < search.scope_id_upper_bound
            ):
                break
            suffix_at = cursor + layout.entry_core_bytes
            null_end = suffix_at + len(layout.null_suffix)
            linked = False
            if null_end <= end and game_db[suffix_at:null_end] == layout.null_suffix:
                next_cursor = null_end
            elif (
                cursor + layout.linked_entry_bytes <= end
                and all(
                    game_db[cursor + offset] == value for offset, value in layout.linked_signature
                )
                and game_db[cursor + layout.linked_flag_offset] in layout.linked_flag_values
                and decode_date(game_db, cursor + layout.linked_date_offset) is not None
            ):
                next_cursor = cursor + layout.linked_entry_bytes
                linked = True
            else:
                break
            if linked:
                code = values[search.scope_code_index]
                pending.append(
                    (
                        position,
                        cursor,
                        SuspensionEntry(
                            search.scope_by_code.get(code, SuspensionScope.UNKNOWN),
                            code,
                            scope_id,
                            issued,
                            values[search.e7_index],
                        ),
                    )
                )
            cursor = next_cursor
        else:
            yield from pending


def suspension_stats(
    entries_by_position: Mapping[int, tuple[SuspensionEntry, ...]], player_count: int, clock: date
) -> SuspensionStats:
    """Count the located entries for the suspension checks: entries, players with an entry,
    entries whose scope code is one the layout lists, and the dates against the save's
    in-game date.

    The date is counted over the bans covering ONE COMPETITION alone. A ban covering a whole
    nation is routinely dated ahead of the clock -- by one to ten days on the save states
    measured -- so counting those makes a career's own fixture list look like a misread date.
    Every save state measured holds zero competition-scope entries dated ahead, which is what
    the bound judges; the nation-scope ones are reported as an anomaly instead.
    """
    entry_count = 0
    competition_entries = 0
    competition_issued_after_clock = 0
    nation_issued_after_clock = 0
    with_known_scope = 0
    for entries in entries_by_position.values():
        entry_count += len(entries)
        for entry in entries:
            dated_ahead = entry.issued > clock
            if entry.scope is SuspensionScope.COMPETITION:
                competition_entries += 1
                competition_issued_after_clock += dated_ahead
            elif entry.scope is SuspensionScope.NATION:
                nation_issued_after_clock += dated_ahead
            if entry.scope is not SuspensionScope.UNKNOWN:
                with_known_scope += 1
    return SuspensionStats(
        players=player_count,
        entries=entry_count,
        players_with_entries=len(entries_by_position),
        competition_entries=competition_entries,
        competition_issued_after_clock=competition_issued_after_clock,
        nation_issued_after_clock=nation_issued_after_clock,
        entries_with_known_scope=with_known_scope,
    )


def named_entries(
    entries_by_position: Mapping[int, tuple[SuspensionEntry, ...]],
    name_for: Callable[[int | None], str | None],
) -> dict[int, tuple[SuspensionEntry, ...]]:
    """The same entries with `competition_name` filled in, keyed as they were.

    `name_for` is `CompetitionIndex.name_for`, the one lookup that names a competition, so a
    ban is named by exactly the rule that names its competition and this module repeats none
    of it. It is asked only for a ban whose scope is COMPETITION: a nation-wide ban's id is a
    nation id, and looking it up would name the ban after whatever competition happens to
    share its number. Naming here, on the located entries, gives `Player.suspensions` and the
    `suspensions()` rows the same name from the same lookup.
    """
    return {
        position: tuple(
            entry
            if entry.competition_id is None
            else replace(entry, competition_name=name_for(entry.competition_id))
            for entry in entries
        )
        for position, entries in entries_by_position.items()
    }


def player_suspensions(entries: Sequence[SuspensionEntry]) -> tuple[PlayerSuspension, ...]:
    """The `Player.suspensions` value for one player's located entries."""
    return tuple(
        PlayerSuspension(
            entry.scope,
            entry.scope_code,
            entry.competition_id,
            entry.competition_name,
            entry.nation_id,
            entry.issued,
        )
        for entry in entries
    )


def suspension_rows(player: Player, entries: Sequence[SuspensionEntry]) -> list[Suspension]:
    """One `Suspension` row per entry, joined to the decoded player and its current club."""
    return [
        Suspension(
            player.uid,
            player.name,
            player.club_uid,
            player.club_name,
            entry.scope,
            entry.scope_code,
            entry.competition_id,
            entry.competition_name,
            entry.nation_id,
            entry.issued,
            FrozenMapping({"e7": entry.e7}),
        )
        for entry in entries
    ]
