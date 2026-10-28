"""Bounded archive/list decoding with ownership from validated person blocks."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass

from fm26save._core._container import ContainerIndex, read_region_frame, region_frame_heads
from fm26save._core._errors import ReaderCheckError
from fm26save._core._layouts import SeasonHistoryLayout, SeasonStatsLayout, find_layout
from fm26save._core._reader_stats import SeasonHistoryStats
from fm26save._core.models.clubs import Club
from fm26save._core.models.season_history import PlayerSeasonHistory
from fm26save._core.models.season_stats import SeasonStatsKind
from fm26save._core.readers._common import SPAN_REGION, layout_mismatch
from fm26save._core.readers.season_stats import SeasonPlayer, decode_season_line, season_club_fields

ARCHIVE_SECTION = "player_stats_hist_dt"
_U32 = struct.Struct("<I")
_METADATA = struct.Struct("<IHIH")
_ABSENT = 0xFFFFFFFF


@dataclass(frozen=True, slots=True)
class HistoryIndex:
    """Complete stored index, with offsets decoded independently of player ownership."""

    singles: tuple[int, ...]
    lists: tuple[tuple[int, ...], ...]
    free: tuple[int, ...]


def find_history_layout(build: str) -> SeasonHistoryLayout:
    """Use this build's history layout, falling back to the known build."""
    return find_layout(SeasonHistoryLayout, SPAN_REGION, None, build).layout


def _mismatch(file_name: str, detail: str) -> ReaderCheckError:
    return layout_mismatch(file_name, detail, "historical season statistics")


def walk_history_index(
    body: bytes, file_name: str, layout: SeasonHistoryLayout | None = None
) -> HistoryIndex:
    """Walk the entire index, bounding every count before reading its words."""
    layout = find_history_layout("") if layout is None else layout
    if not body.startswith(layout.index_header):
        raise _mismatch(file_name, "the history index does not start with its header")
    position = len(layout.index_header)
    end = len(body)

    def word() -> int:
        nonlocal position
        if position + _U32.size > end:
            raise _mismatch(file_name, "a history index word runs past the frame")
        value: int = _U32.unpack_from(body, position)[0]
        position += _U32.size
        return value

    def words(*, adjacent: bool = False) -> tuple[int, ...]:
        nonlocal position
        count = word()
        if count > (end - position) // _U32.size:
            raise _mismatch(file_name, "a history index count runs past the frame")
        result: list[int] = []
        previous = 0
        for _ in range(count):
            value = word()
            result.append((value + previous) & _ABSENT if adjacent else value)
            previous = value
        return tuple(result)

    singles = words()
    list_count = word()
    if list_count > (end - position) // _U32.size:
        raise _mismatch(file_name, "the history list count runs past the frame")
    lists = tuple(words(adjacent=True) for _ in range(list_count))
    free = words()
    if word() != layout.unit_bytes:
        raise _mismatch(file_name, "the history index has an unexpected archive unit size")
    if body[position:] != layout.footer:
        raise _mismatch(file_name, "the history index footer does not end the frame")
    return HistoryIndex(singles, lists, free)


def read_history_index(index: ContainerIndex, layout: SeasonHistoryLayout) -> HistoryIndex:
    """Accept exactly one matching span frame whose complete structure walks."""
    accepted: HistoryIndex | None = None
    first_error: ReaderCheckError | None = None
    candidates = 0
    for span, head in region_frame_heads(index, SPAN_REGION, len(layout.index_header)):
        if head != layout.index_header:
            continue
        candidates += 1
        try:
            walked = walk_history_index(
                read_region_frame(index, SPAN_REGION, span), index.file_name, layout
            )
        except ReaderCheckError as error:
            if first_error is None:
                first_error = error
            continue
        if accepted is not None:
            raise _mismatch(index.file_name, "2 frames each walk as the history index")
        accepted = walked
    if accepted is None:
        if first_error is not None:
            raise first_error
        raise _mismatch(index.file_name, f"no history index frame found ({candidates} candidates)")
    return accepted


def history_selector(
    game_db: bytes,
    block_start: int | None,
    window_start: int,
    window_end: int,
    layout: SeasonHistoryLayout,
) -> int:
    """Read a selector only beside a person block accepted within its owning player window."""
    if block_start is None:
        return _ABSENT
    offset = block_start + layout.selector_offset_from_block_start
    if not window_start <= offset or offset + _U32.size > window_end:
        return _ABSENT
    value: int = _U32.unpack_from(game_db, offset)[0]
    return value


def build_history(
    index: HistoryIndex,
    archive: bytes,
    selectors: Mapping[int, int],
    players: Mapping[int, SeasonPlayer],
    team_to_club: Mapping[int, tuple[int, int]],
    club_by_uid: Mapping[int, Club],
    stat_layout: SeasonStatsLayout,
    file_name: str,
    layout: SeasonHistoryLayout | None = None,
) -> tuple[tuple[PlayerSeasonHistory, ...], SeasonHistoryStats]:
    """Validate every envelope and reference, then decode the rows with proven ownership."""
    layout = find_history_layout("") if layout is None else layout
    header_bytes = len(layout.archive_header)
    payload_bytes = len(archive) - header_bytes
    if not archive.startswith(layout.archive_header) or payload_bytes % layout.unit_bytes:
        raise _mismatch(file_name, "the history archive header or unit alignment is invalid")
    unit_count = payload_bytes // layout.unit_bytes
    for offset in range(header_bytes, len(archive), layout.unit_bytes):
        if archive[offset] != 0 or archive[offset + 31] >= len(layout.kind_names):
            raise _mismatch(file_name, "a history archive unit has an unexpected marker or kind")

    def unit_number(offset: int) -> int:
        if offset % layout.unit_bytes or not 0 <= offset < payload_bytes:
            raise _mismatch(file_name, "a history reference is unaligned or outside the archive")
        return offset // layout.unit_bytes

    # A byte per archive unit bounds duplicate detection without a second integer index.
    referenced = bytearray(unit_count)
    for offset in index.singles:
        number = unit_number(offset)
        if referenced[number]:
            raise _mismatch(file_name, "history singles repeat an archive reference")
        referenced[number] = 1
    for offsets in index.lists:
        for offset in offsets:
            number = unit_number(offset)
            if referenced[number]:
                raise _mismatch(file_name, "history lists or singles repeat an archive reference")
            referenced[number] = 1

    owners: dict[int, int] = {}
    players_without_history = 0
    for uid, player in players.items():
        selector = selectors.get(uid, _ABSENT)
        if selector == _ABSENT:
            players_without_history += 1
            continue
        if not 0 <= selector < len(index.lists):
            raise _mismatch(file_name, "a player's history selector is outside the list index")
        if not index.lists[selector]:
            players_without_history += 1
            continue
        if selector in owners:
            raise _mismatch(file_name, "players share a nonempty history list")
        owners[selector] = uid

    rows: list[PlayerSeasonHistory] = []
    owned_units = 0
    unresolved_teams = 0
    kinds = tuple(SeasonStatsKind(name) for name in layout.kind_names)
    for selector, uid in owners.items():
        player = players[uid]
        for offset in index.lists[selector]:
            at = header_bytes + offset
            team_id, competition, _unknown, year = _METADATA.unpack_from(archive, at + 1)
            team_id = None if team_id == _ABSENT else team_id
            club_fields = season_club_fields(team_id, team_to_club, club_by_uid)
            unresolved_teams += club_fields[0] is None
            line = bytearray(stat_layout.line_bytes)
            line[:2] = stat_layout.line_marker
            line[2:6] = archive[at + 13 : at + 17]
            line[6:11] = archive[at + 24 : at + 29]
            line[11:14] = archive[at + 17 : at + 20]
            line[14] = archive[at + 29]
            line[15:19] = archive[at + 20 : at + 24]
            line[19:139] = archive[at + 32 : at + 152]
            rows.append(
                PlayerSeasonHistory(
                    player.uid,
                    player.name,
                    kinds[archive[at + 31]],
                    team_id,
                    *club_fields,
                    *decode_season_line(bytes(line), 0, player.goalkeeper, stat_layout),  # pyright: ignore[reportArgumentType]
                    season_year=year,
                    competition_reference=competition,
                )
            )
            owned_units += 1
    return tuple(rows), SeasonHistoryStats(
        rows=len(rows),
        archive_units=unit_count,
        unowned_units=unit_count - owned_units,
        lists=len(index.lists),
        unowned_lists=sum(bool(items) for i, items in enumerate(index.lists) if i not in owners),
        players_without_history=players_without_history,
        unresolved_teams=unresolved_teams,
    )
