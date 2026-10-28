"""Counted, owned match summaries used only to enrich missing fixture scores."""

from __future__ import annotations

import datetime
import functools
import re
import struct
from dataclasses import dataclass

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import MatchSummaryLayout, find_layout
from fm26save._core._scan import decode_date
from fm26save._core.readers._common import GAME_DB_SECTION

type MatchSummaryKey = tuple[datetime.date, int, int, int]
type ScorePair = tuple[int, int]

_WORD = struct.Struct("<I")


@dataclass(frozen=True, slots=True)
class MatchSummaryScores:
    """Scores from complete objects; a poisoned key can never supply enrichment."""

    scores: FrozenMapping[MatchSummaryKey, ScorePair | None]
    lists_found: int
    lists_decoded: int
    record_count: int
    invalid_score_records: int


def find_match_summary_layout(game_db_schema: int | None, build: str) -> MatchSummaryLayout:
    return find_layout(MatchSummaryLayout, GAME_DB_SECTION, game_db_schema, build).layout


@functools.cache
def _header_pattern(layout: MatchSummaryLayout) -> tuple[re.Pattern[bytes], int]:
    constraints = {layout.kind_offset: re.escape(bytes([layout.kind_value]))}
    for offset in layout.ability_offsets:
        low, high = layout.ability_range
        if not 0 <= low <= high <= 255:
            raise ValueError("summary ability locator must fit a byte")
        constraints[offset] = rb"[" + re.escape(bytes(range(low, high + 1))) + rb"]"
        constraints[offset + 1] = b"\x00"
    low, high = layout.attributes_range
    attribute = rb"[" + re.escape(bytes(range(low, high + 1))) + rb"]"
    for offset in range(
        layout.attributes_offset, layout.attributes_offset + layout.attributes_count
    ):
        constraints[offset] = attribute
    for offset in layout.flag_offsets:
        constraints[offset] = rb"[\x00\x01]"
    first, last = min(constraints), max(constraints)
    if first < 0 or last >= layout.header_bytes:
        raise ValueError("summary locator lies outside its header")
    return re.compile(
        b"".join(constraints.get(i, b".") for i in range(first, last + 1)), re.DOTALL
    ), first


def _sound_header(db: bytes, at: int, layout: MatchSummaryLayout) -> bool:
    uid = _WORD.unpack_from(db, at + layout.uid_offset)[0]
    if uid in (0, 0xFFFFFFFF) or uid != _WORD.unpack_from(db, at + layout.uid_copy_offset)[0]:
        return False
    return _WORD.unpack_from(db, at + layout.header_word_offset)[0] in layout.header_word_values


def _walk_object(
    db: bytes, at: int, count: int, layout: MatchSummaryLayout
) -> tuple[list[tuple[MatchSummaryKey, ScorePair]], int] | None:
    end = len(db)
    offset = at + layout.header_bytes
    if count > (end - offset) // layout.record_bytes:
        return None
    rows: list[tuple[MatchSummaryKey, ScorePair]] = []
    for _ in range(count):
        if db[offset + layout.lead_byte_offset] != layout.lead_byte_value:
            return None
        date = decode_date(db, offset + layout.date_offset)
        competition = _WORD.unpack_from(db, offset + layout.competition_id_offset)[0]
        home = _WORD.unpack_from(db, offset + layout.home_team_id_offset)[0]
        away = _WORD.unpack_from(db, offset + layout.away_team_id_offset)[0]
        if date is None:
            return None
        score = (db[offset + layout.home_goals_offset], db[offset + layout.away_goals_offset])
        rows.append(((date, competition, home, away), score))
        offset += layout.record_bytes
    for _ in range(layout.trailing_array_count):
        if offset + _WORD.size > end:
            return None
        words = _WORD.unpack_from(db, offset)[0]
        offset += _WORD.size
        if words > (end - offset) // _WORD.size:
            return None
        offset += words * _WORD.size
    if offset + 4 > end:
        return None
    if db[offset : offset + 4] != layout.null_date_bytes and decode_date(db, offset) is None:
        return None
    return rows, offset + 4


def locate_match_summary_scores(db: bytes, layout: MatchSummaryLayout) -> MatchSummaryScores:
    """Require the complete header, declared rows, and closing collection grammar.

    A bad statistical value still belongs to a structurally sound row. It poisons that
    exact fixture key, as does any conflicting duplicate, without changing the count walk.
    """
    pattern, back = _header_pattern(layout)
    scores: dict[MatchSummaryKey, ScorePair | None] = {}
    found = decoded = records = invalid = 0
    start = 0
    while (hit := pattern.search(db, start)) is not None:
        start = hit.start() + 1
        at = hit.start() - back
        if at < 0 or at + layout.header_bytes > len(db) or not _sound_header(db, at, layout):
            continue
        found += 1
        count = db[at + layout.count_offset]
        walked = _walk_object(db, at, count, layout)
        if walked is None:
            continue
        rows, start = walked
        decoded += 1
        records += count
        for key, pair in rows:
            if max(pair) > layout.goals_maximum:
                invalid += 1
                scores[key] = None
            elif key not in scores:
                scores[key] = pair
            elif scores[key] != pair:
                scores[key] = None
    return MatchSummaryScores(FrozenMapping(scores), found, decoded, records, invalid)
