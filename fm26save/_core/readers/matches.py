"""Read complete counted per-match histories within player objects.

A marker and byte count enclose contiguous team lists. Each ten-byte child header carries
an observed marker, a raw team word and the number of records.
Records without performance data are fifteen bytes; records with a body are fifty-four.
The full declared parent is walked before any rows are emitted. Year and identity bounds
filter output, while implausible statistics remain visible for validation.
"""

from __future__ import annotations

import datetime
import functools
import re
import struct
from bisect import bisect_right
from collections.abc import Mapping
from dataclasses import dataclass

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import MatchRecordLayout, find_layout
from fm26save._core._reader_stats import MatchStats
from fm26save._core._scan import decode_date
from fm26save._core.models.clubs import Club
from fm26save._core.models.common import CodedValue
from fm26save._core.models.matches import MatchPosition, PlayerMatchStats
from fm26save._core.models.players import Player
from fm26save._core.readers._common import GAME_DB_SECTION, MISSING_REFERENCE, build_gap_padded_struct
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.match_cache import CacheDeclarations, MatchCacheWalker
from fm26save._core.readers.player_scan import PlayerRecords
from fm26save._core.readers.stages import StageIndex
from fm26save._core.table import Table

# The key a record is filed under when it lies before the first player's window and so belongs
# to no player. Such a record is counted and then dropped: nothing is built from it.
#
# This count is structurally zero, and the guard behind it is still worth keeping. The search
# starts where the first player's window starts, so no record it can reach bisects below the
# first player, and every save measured files none here. What the guard prevents is worse than
# an undercount: a position of -1 indexes the *last* player's uid, so were the region ever to
# start earlier, a record before the first window would be credited to the wrong player in
# silence. It is not dead code; do not remove it because the count never moves.
UNOWNED_POSITION = -1

_DATE_BYTES = 4
# How wide the position mask is, which bounds the bits a layout may name.
_POSITION_MASK_BITS = 16
_NO_BODY_FLAG = 0
_BODY_FLAG = 1
# What a body stores for a player who was on the pitch at the final whistle, and for a match the
# game rated nobody in. Neither is a minute or a rating, so neither is shipped as one.
_NEVER_LEFT_THE_PITCH = 0
_NOBODY_WAS_RATED = 0

_NO_OPPONENT_CLUB: tuple[int | None, str | None, str | None, int | None] = (None, None, None, None)


@dataclass(frozen=True, slots=True)
class RawMatchRecord:
    """One accepted per-match record, before any join.

    Every field from `position_mask` on is None when `has_stats` is false, because the record
    then stops before them and those bytes belong to the next match.

    Attributes:
        date: The date the match was played.
        opponent_team_id: The opposing side's first-team id, exactly as stored.
        competition_id: The competition id, in the stage id space.
        tag: The unidentified byte exported as `unknown["tag"]`.
        has_stats: Whether a performance body follows the header.
        position_mask: The stored position mask.
        role_code: The unidentified byte exported as `unknown["role_code"]`.
        goals: Goals scored.
        assists: Assists, which is a hypothesis with no labelled source.
        left_at_minute: The minute the player left the pitch, stored as 0 for a player who was
            on it at the final whistle.
        minutes: Minutes played.
        rating_raw: The match rating before it is divided by the layout's scale, stored as 0
            for a match the game rated nobody in.
        passes_attempted: Passes attempted.
        passes_completed: Passes completed.
    """

    date: datetime.date
    opponent_team_id: int
    competition_id: int
    tag: int
    has_stats: bool
    position_mask: int | None
    role_code: int | None
    goals: int | None
    assists: int | None
    left_at_minute: int | None
    minutes: int | None
    rating_raw: int | None
    passes_attempted: int | None
    passes_completed: int | None


@dataclass(frozen=True, slots=True)
class _MatchSearch:
    """Everything `locate_match_records` needs from a layout and a clock year, derived once.

    `list_pattern` finds the counted-list header. `header_struct`
    unpacks the fields every record carries and `body_struct` those only a record with a body
    carries; both unpack from the record start, and the `*_index` fields give each value's
    position in its result.
    """

    list_pattern: re.Pattern[bytes]
    parent_pattern: re.Pattern[bytes]
    list_header_struct: struct.Struct
    list_header_bytes: int
    header_struct: struct.Struct
    opponent_team_id_index: int
    competition_id_index: int
    tag_index: int
    body_flag_index: int
    body_struct: struct.Struct
    position_mask_index: int
    role_code_index: int
    goals_index: int
    assists_index: int
    left_at_index: int
    minutes_index: int
    rating_index: int
    passes_attempted_index: int
    passes_completed_index: int
    date_offset: int
    lead_byte_value: int
    header_bytes: int
    record_bytes: int
    owner_back_offset: int
    lowest_team_id: int
    highest_team_id: int
    lowest_competition_id: int
    highest_competition_id: int


def find_match_record_layout(game_db_schema: int | None, build: str) -> MatchRecordLayout:
    """Look up the per-match record layout for a `game_db` schema, falling back to the build."""
    return find_layout(MatchRecordLayout, GAME_DB_SECTION, game_db_schema, build).layout


@functools.cache
def _match_search(layout: MatchRecordLayout, clock_year: int) -> _MatchSearch:
    """The layout's compiled search and structs for one in-game year, built on first use.

    Raises:
        ValueError: The lead byte does not start a record, the date does not lie inside the
            header, the header is not shorter than a whole record, a header field ends past the
            header, a body field starts inside the header or ends past the record, two fields
            overlap, the years around the clock are none, or a bound leaves no id.
    """
    if layout.lead_byte_offset != 0:
        raise ValueError(
            f"the lead byte at offset {layout.lead_byte_offset} must start a record, since the "
            "search anchors on it"
        )
    if layout.header_bytes >= layout.record_bytes:
        raise ValueError(
            f"the {layout.header_bytes}-byte header must be shorter than the "
            f"{layout.record_bytes}-byte record, which is the header plus a body"
        )
    if layout.date_offset <= layout.lead_byte_offset:
        raise ValueError(f"the date at offset {layout.date_offset} must follow the lead byte")
    if layout.date_offset + _DATE_BYTES > layout.header_bytes:
        raise ValueError(
            f"the date at offset {layout.date_offset} ends past the {layout.header_bytes}-byte "
            "header, which every record carries whole"
        )
    if layout.years_before_clock + layout.years_after_clock + 1 <= 0:
        raise ValueError("the match search holds no year")

    header_specs = [
        (layout.opponent_team_id_offset, "I", "opponent_team_id"),
        (layout.competition_id_offset, "I", "competition_id"),
        (layout.tag_offset, "B", "tag"),
        (layout.body_flag_offset, "B", "body_flag"),
    ]
    body_specs = [
        (layout.position_mask_offset, "H", "position_mask"),
        (layout.role_code_offset, "B", "role_code"),
        (layout.goals_offset, "B", "goals"),
        (layout.assists_offset, "B", "assists"),
        (layout.left_at_offset, "B", "left_at_minute"),
        (layout.minutes_offset, "B", "minutes"),
        (layout.rating_offset, "B", "rating"),
        (layout.passes_attempted_offset, "B", "passes_attempted"),
        (layout.passes_completed_offset, "B", "passes_completed"),
    ]
    for offset, format_code, field_name in header_specs:
        if offset + struct.calcsize(format_code) > layout.header_bytes:
            raise ValueError(
                f"header field {field_name!r} at offset {offset} ends past the "
                f"{layout.header_bytes}-byte header, which every record carries whole"
            )
    for offset, format_code, field_name in body_specs:
        if offset < layout.header_bytes:
            raise ValueError(
                f"body field {field_name!r} at offset {offset} starts inside the "
                f"{layout.header_bytes}-byte header, so a record with no body would appear to "
                "carry one"
            )
        if offset + struct.calcsize(format_code) > layout.record_bytes:
            raise ValueError(
                f"body field {field_name!r} at offset {offset} ends past the "
                f"{layout.record_bytes}-byte record"
            )
    header_struct, _header_start, header_indexes = build_gap_padded_struct(
        header_specs, start_offset=0
    )
    body_struct, _body_start, body_indexes = build_gap_padded_struct(body_specs, start_offset=0)

    lowest_team_id, highest_team_id = layout.team_id_range
    if highest_team_id < lowest_team_id:
        raise ValueError(f"team_id_range {layout.team_id_range} leaves no team id")
    lowest_competition_id, highest_competition_id = layout.competition_id_range
    if highest_competition_id < lowest_competition_id:
        raise ValueError(
            f"competition_id_range {layout.competition_id_range} leaves no competition id"
        )
    if not layout.list_markers or any(len(marker) != 2 for marker in layout.list_markers):
        raise ValueError("match lists need explicit two-byte markers")
    list_header_struct, _, list_indexes = build_gap_padded_struct(
        [(layout.list_team_id_offset, "I", "team"), (layout.list_count_offset, "I", "count")],
        start_offset=0,
    )
    if list_header_struct.size != layout.list_header_bytes or list_indexes != {
        "team": 0,
        "count": 1,
    }:
        raise ValueError("match list fields must fill the list header after its marker")
    if layout.list_team_id_offset != 2:
        raise ValueError("match list team field must follow the two-byte marker")
    list_pattern = re.compile(
        b"(?:"
        + b"|".join(re.escape(marker) for marker in layout.list_markers)
        + b")"
        + b".{%d}" % (layout.list_header_bytes - 2)
        + re.escape(bytes((layout.lead_byte_value,))),
        re.DOTALL,
    )
    if layout.parent_header_bytes != len(
        layout.parent_marker
    ) + 1 or layout.parent_count_offset != len(layout.parent_marker):
        raise ValueError("match parent must contain its marker followed by a byte count")
    parent_pattern = re.compile(
        re.escape(layout.parent_marker) + rb"[\x01-\xff]" + list_pattern.pattern, re.DOTALL
    )
    return _MatchSearch(
        list_pattern=list_pattern,
        parent_pattern=parent_pattern,
        list_header_struct=list_header_struct,
        list_header_bytes=layout.list_header_bytes,
        header_struct=header_struct,
        opponent_team_id_index=header_indexes["opponent_team_id"],
        competition_id_index=header_indexes["competition_id"],
        tag_index=header_indexes["tag"],
        body_flag_index=header_indexes["body_flag"],
        body_struct=body_struct,
        position_mask_index=body_indexes["position_mask"],
        role_code_index=body_indexes["role_code"],
        goals_index=body_indexes["goals"],
        assists_index=body_indexes["assists"],
        left_at_index=body_indexes["left_at_minute"],
        minutes_index=body_indexes["minutes"],
        rating_index=body_indexes["rating"],
        passes_attempted_index=body_indexes["passes_attempted"],
        passes_completed_index=body_indexes["passes_completed"],
        date_offset=layout.date_offset,
        lead_byte_value=layout.lead_byte_value,
        header_bytes=layout.header_bytes,
        record_bytes=layout.record_bytes,
        owner_back_offset=layout.owner_back_offset,
        lowest_team_id=lowest_team_id,
        highest_team_id=highest_team_id,
        lowest_competition_id=lowest_competition_id,
        highest_competition_id=highest_competition_id,
    )


class LocatedMatchRecords(dict[int, tuple[RawMatchRecord, ...]]):
    """Owned match lists and their structural completeness, before joins."""

    def __init__(
        self,
        records: Mapping[int, tuple[RawMatchRecord, ...]],
        *,
        lists_found: int,
        lists_decoded: int,
        history_declarations: CacheDeclarations | None = None,
    ) -> None:
        super().__init__(records)
        self.lists_found = lists_found
        self.lists_decoded = lists_decoded
        self.history_declarations = history_declarations


def _cache_declarations(
    game_db: bytes,
    player_records: PlayerRecords,
    layout: MatchRecordLayout,
    search: _MatchSearch,
) -> CacheDeclarations | None:
    """Count owned declarations independently of emitted rows and output filters."""
    if layout.cache_layout is None:
        return None
    walker = MatchCacheWalker(layout.cache_layout)
    counts = {"containing_null": 0, "null": 0, "empty": 0, "nonempty": 0, "unknown": 0}
    offsets = player_records.record_offsets
    for position, ability in enumerate(offsets):
        end = (
            offsets[position + 1] - search.owner_back_offset
            if position + 1 < len(offsets)
            else len(game_db)
        )
        declaration = walker.locate(game_db, ability, end)
        state = declaration.state
        if state == "empty" and declaration.offset is not None:
            at = declaration.offset + layout.parent_header_bytes
            # Retain the nonempty parent's complete-extra-child contradiction control.
            # A following marker alone may belong to another property and proves nothing.
            if at + search.list_header_bytes <= end and game_db[at : at + 2] in layout.list_markers:
                _team, count = search.list_header_struct.unpack_from(game_db, at)
                at += search.list_header_bytes
                if 0 < count <= (end - at) // search.header_bytes:
                    for _ in range(count):
                        decoded = _read_match_record(game_db, at, search, end)
                        if decoded is None:
                            break
                        at += decoded[1]
                    else:
                        state = "unknown"
        counts[state] += 1
    return CacheDeclarations(slots=len(offsets), **counts)


def _read_match_record(
    game_db: bytes, at: int, search: _MatchSearch, end: int
) -> tuple[RawMatchRecord, int] | None:
    """Read framing separately from output ID/year bounds and statistic sanity checks."""
    if at + search.header_bytes > end or game_db[at] != search.lead_byte_value:
        return None
    played_on = decode_date(game_db, at + search.date_offset)
    if played_on is None:
        return None
    h = search.header_struct.unpack_from(game_db, at)
    flag = h[search.body_flag_index]
    if flag not in (_NO_BODY_FLAG, _BODY_FLAG):
        return None
    size = search.record_bytes if flag else search.header_bytes
    if at + size > end:
        return None
    b = search.body_struct.unpack_from(game_db, at) if flag else None
    return RawMatchRecord(
        date=played_on,
        opponent_team_id=h[search.opponent_team_id_index],
        competition_id=h[search.competition_id_index],
        tag=h[search.tag_index],
        has_stats=bool(flag),
        position_mask=None if b is None else b[search.position_mask_index],
        role_code=None if b is None else b[search.role_code_index],
        goals=None if b is None else b[search.goals_index],
        assists=None if b is None else b[search.assists_index],
        left_at_minute=None if b is None else b[search.left_at_index],
        minutes=None if b is None else b[search.minutes_index],
        rating_raw=None if b is None else b[search.rating_index],
        passes_attempted=None if b is None else b[search.passes_attempted_index],
        passes_completed=None if b is None else b[search.passes_completed_index],
    ), size


def locate_match_records(
    game_db: bytes, player_records: PlayerRecords, layout: MatchRecordLayout, clock: datetime.date
) -> LocatedMatchRecords:
    """Read complete counted match lists within each player's ownership window.

    The parent marker and byte count enclose contiguous child lists. Each observed child
    marker precedes a raw team word and a record count. Every child must frame completely,
    including records outside the output year/ID window, before any sibling is emitted.
    Those output bounds do not determine where a list ends. Statistic values never decide
    framing: a genuine record with a bad rating remains visible to the validation checks.
    A separate bounded field walk establishes owned null/empty cache declarations. Its
    counts are independent of this nonempty scan and its output filters; unsupported
    preceding fields remain unknown.
    """
    search = _match_search(layout, clock.year)
    offsets = player_records.record_offsets
    if not offsets:
        return LocatedMatchRecords(
            {},
            lists_found=0,
            lists_decoded=0,
            history_declarations=_cache_declarations(game_db, player_records, layout, search),
        )
    start = max(0, offsets[0] - search.owner_back_offset)
    records_by_position: dict[int, list[RawMatchRecord]] = {}
    lists_found = lists_decoded = 0
    suffix_lengths: dict[int, int] = {}
    suffix_owner: int | None = None

    def walk_child(first_at: int, count: int, end: int) -> tuple[list[RawMatchRecord], int] | None:
        if count > (end - first_at) // search.header_bytes:
            return None
        at = first_at
        records: list[RawMatchRecord] = []
        visited: list[int] = []
        available = 0
        for index in range(count):
            known_length = suffix_lengths.get(at)
            if known_length is not None and count - index > known_length:
                available = known_length
                break
            decoded = _read_match_record(game_db, at, search, end)
            if decoded is None:
                suffix_lengths[at] = 0
                break
            visited.append(at)
            record, size = decoded
            at += size
            if (
                clock.year - layout.years_before_clock
                <= record.date.year
                <= clock.year + layout.years_after_clock
                and search.lowest_team_id <= record.opponent_team_id <= search.highest_team_id
                and search.lowest_competition_id
                <= record.competition_id
                <= search.highest_competition_id
            ):
                records.append(record)
        else:
            return records, at
        # A failed walk establishes the exact valid suffix length at each visited start.
        # Reusing those lengths avoids walking the same malformed suffix for nested headers;
        # a shorter claim can still decode, so genuine overlapping lists remain discoverable.
        for record_at in reversed(visited):
            available += 1
            suffix_lengths[record_at] = available
        return None

    while (hit := search.parent_pattern.search(game_db, start)) is not None:
        parent_at = hit.start()
        start = parent_at + 1
        list_at = parent_at + layout.parent_header_bytes
        first_at = list_at + search.list_header_bytes
        position = bisect_right(offsets, first_at + search.owner_back_offset) - 1
        end = (
            offsets[position + 1] - search.owner_back_offset
            if position + 1 < len(offsets)
            else len(game_db)
        )
        owned_start = max(0, offsets[position] - search.owner_back_offset)
        if parent_at < owned_start or first_at + search.header_bytes > end:
            continue
        if decode_date(game_db, first_at + search.date_offset) is None:
            continue
        first_header = search.header_struct.unpack_from(game_db, first_at)
        if (
            not search.lowest_team_id
            <= first_header[search.opponent_team_id_index]
            <= search.highest_team_id
        ):
            continue
        first_competition = first_header[search.competition_id_index]
        if not (
            0 <= first_competition <= search.highest_competition_id
            or first_competition == MISSING_REFERENCE
        ):
            continue
        child_count = game_db[parent_at + layout.parent_count_offset]
        lists_found += child_count
        if position != suffix_owner:
            suffix_lengths.clear()
            suffix_owner = position
        records: list[RawMatchRecord] = []
        for _ in range(child_count):
            if (
                list_at + search.list_header_bytes > end
                or game_db[list_at : list_at + 2] not in layout.list_markers
            ):
                break
            # The team word is a raw reference, not a structural boundary. Zero occurs in
            # complete owned histories and does not prevent decoding its sibling lists.
            _team, count = search.list_header_struct.unpack_from(game_db, list_at)
            if count == 0:
                # No independently anchored empty-history grammar has been established.
                break
            walked = walk_child(list_at + search.list_header_bytes, count, end)
            if walked is None:
                break
            child_records, list_at = walked
            records.extend(child_records)
            # A completely framed child cannot contain another history parent. Skip its
            # bytes on retry even if a later sibling fails; failed children retain the
            # suffix memo and nested recovery path above.
            start = list_at
        else:
            # A complete additional child at the exact continuation contradicts the parent
            # count. Marker bytes alone are insufficient: a following property may share
            # them, so require the whole additional child before rejecting this parent.
            if (
                list_at + search.list_header_bytes <= end
                and game_db[list_at : list_at + 2] in layout.list_markers
            ):
                _team, extra_count = search.list_header_struct.unpack_from(game_db, list_at)
                if extra_count:
                    extra = walk_child(list_at + search.list_header_bytes, extra_count, end)
                    if extra is not None:
                        start = extra[1]
                        continue
            lists_decoded += child_count
            start = list_at
            if records:
                records_by_position.setdefault(position, []).extend(records)
    return LocatedMatchRecords(
        {position: tuple(records) for position, records in records_by_position.items()},
        lists_found=lists_found,
        lists_decoded=lists_decoded,
        history_declarations=_cache_declarations(game_db, player_records, layout, search),
    )


@functools.cache
def _position_labels(
    position_bits: tuple[tuple[int, str], ...],
) -> FrozenMapping[int, MatchPosition]:
    """The whole mask each named bit stands for, mapped to its position.

    Keying on the whole mask rather than on the bit is what makes the lookup total: a mask with
    no bit, with a bit no pair names, or with more than one bit is simply absent, and every one
    of those reads as UNKNOWN with its raw mask kept.

    Raises:
        ValueError: A bit is outside the mask, a bit is named twice, or a name is not a
            `MatchPosition` member.
    """
    labels: dict[int, MatchPosition] = {}
    for bit, member_name in position_bits:
        if not 0 <= bit < _POSITION_MASK_BITS:
            raise ValueError(
                f"position bit {bit} is outside the {_POSITION_MASK_BITS}-bit position mask"
            )
        mask = 1 << bit
        if mask in labels:
            raise ValueError(f"position bit {bit} is named twice")
        try:
            labels[mask] = MatchPosition[member_name]
        except KeyError:
            raise ValueError(
                f"position bit {bit} names {member_name!r}, which is not a MatchPosition member"
            ) from None
    return FrozenMapping(labels)


def _opponent_fields(
    opponent_club: tuple[int, int] | None, club_by_uid: Mapping[int, Club]
) -> tuple[int | None, str | None, str | None, int | None]:
    """(uid, name, short name, slot) of the club fielding the opposing team, all None when no
    club lists that team.
    """
    if opponent_club is None:
        return _NO_OPPONENT_CLUB
    club_uid, team_slot = opponent_club
    club_record = club_by_uid.get(club_uid)
    if club_record is None:
        return club_uid, None, None, team_slot
    return club_uid, club_record.name, club_record.short_name, team_slot


def build_player_match_stats(
    records_by_position: Mapping[int, tuple[RawMatchRecord, ...]],
    player_records: PlayerRecords,
    players: Table[Player],
    club_index: ClubIndex,
    stage_index: StageIndex,
    layout: MatchRecordLayout,
) -> tuple[tuple[PlayerMatchStats, ...], MatchStats]:
    """Join the located records to their players and opponents, and count what the checks judge.

    Rows come back in player order and, inside each player, in the order the save stores his
    matches. A record that belongs to no player builds no row and is counted in
    `MatchStats.unowned`, so `MatchStats.records` counts exactly the rows returned.

    The stage table is read here only to count how many competition ids it names, which is what
    the stage-space check judges. No value of its own reaches a row: a record carries its
    competition id itself, and nothing here looks one up.

    A statistic outside the layout's bounds is flagged and kept, never blanked: `stats_in_range`
    says what fmsave makes of the numbers, and the numbers stay exactly as the save holds them.

    Two stored zeros are not numbers of their own kind and are not shipped as one. A stored
    `left_at_minute` of zero means the player was on the pitch at the final whistle rather than
    that he left in the opening seconds, and a stored rating of zero means the game rated nobody
    in that match rather than that it rated him 0.0; both become None, and the rating's zero is
    kept in `unknown` so the record still says what the save holds.
    """
    labels_by_mask = _position_labels(layout.position_bits)
    uids = player_records.uids
    team_to_club = club_index.team_to_club
    club_by_uid = club_index.club_by_uid
    competition_ids = stage_index.stage_ids_by_competition_id
    maximum_minutes = layout.maximum_minutes
    maximum_rating = layout.maximum_rating
    maximum_goals = layout.maximum_goals
    rating_scale = layout.rating_scale

    rows: list[PlayerMatchStats] = []
    record_count = 0
    with_stats = 0
    players_with_records = 0
    competition_in_stage_space = 0
    minutes_in_range = 0
    rating_in_range = 0
    stats_in_range_count = 0
    opponent_resolved = 0
    unowned = 0

    for position in sorted(records_by_position):
        position_records = records_by_position[position]
        if position == UNOWNED_POSITION:
            unowned += len(position_records)
            continue
        players_with_records += 1
        player_uid: int = uids[position]
        decoded_player = players.get_by_uid(player_uid)
        player_name = None if decoded_player is None else decoded_player.name
        for record in position_records:
            record_count += 1
            if record.competition_id in competition_ids:
                competition_in_stage_space += 1
            opponent_club = team_to_club.get(record.opponent_team_id)
            if opponent_club is not None:
                opponent_resolved += 1
            club_uid, club_name, club_short_name, team_slot = _opponent_fields(
                opponent_club, club_by_uid
            )
            position_mask = record.position_mask
            rating_raw = record.rating_raw
            minutes = record.minutes
            goals = record.goals
            left_at_minute = record.left_at_minute
            stats_in_range = False
            if record.has_stats:
                with_stats += 1
                minutes_ok = minutes is not None and minutes <= maximum_minutes
                rating_ok = rating_raw is not None and rating_raw <= maximum_rating
                goals_ok = goals is not None and goals <= maximum_goals
                minutes_in_range += minutes_ok
                rating_in_range += rating_ok
                stats_in_range = minutes_ok and rating_ok and goals_ok
                stats_in_range_count += stats_in_range
            unknown_values = {"tag": record.tag}
            if record.role_code is not None:
                unknown_values["role_code"] = record.role_code
            if rating_raw is not None and rating_raw == _NOBODY_WAS_RATED:
                unknown_values["rating_raw"] = rating_raw
            rows.append(
                PlayerMatchStats(
                    player_uid=player_uid,
                    player_name=player_name,
                    date=record.date,
                    competition_id=record.competition_id,
                    opponent_team_id=record.opponent_team_id,
                    opponent_club_uid=club_uid,
                    opponent_club_name=club_name,
                    opponent_club_short_name=club_short_name,
                    opponent_team_slot=team_slot,
                    has_stats=record.has_stats,
                    position=(
                        None
                        if position_mask is None
                        else CodedValue(
                            label=labels_by_mask.get(position_mask, MatchPosition.UNKNOWN),
                            raw=position_mask,
                        )
                    ),
                    minutes=minutes,
                    left_at_minute=(
                        None if left_at_minute == _NEVER_LEFT_THE_PITCH else left_at_minute
                    ),
                    goals=goals,
                    assists=record.assists,
                    rating=(
                        None
                        if rating_raw is None or rating_raw == _NOBODY_WAS_RATED
                        else rating_raw / rating_scale
                    ),
                    passes_attempted=record.passes_attempted,
                    passes_completed=record.passes_completed,
                    stats_in_range=stats_in_range,
                    unknown=FrozenMapping(unknown_values),
                )
            )

    declarations = (
        records_by_position.history_declarations
        if isinstance(records_by_position, LocatedMatchRecords)
        else None
    )
    if declarations is not None and declarations.slots != len(player_records.uids):
        declarations = None
    stats = MatchStats(
        records=record_count,
        with_stats=with_stats,
        players_with_records=players_with_records,
        competition_in_stage_space=competition_in_stage_space,
        minutes_in_range=minutes_in_range,
        rating_in_range=rating_in_range,
        stats_in_range=stats_in_range_count,
        opponent_resolved=opponent_resolved,
        unowned=unowned,
        lists_found=records_by_position.lists_found
        if isinstance(records_by_position, LocatedMatchRecords)
        else None,
        lists_decoded=records_by_position.lists_decoded
        if isinstance(records_by_position, LocatedMatchRecords)
        else None,
        history_slots=len(player_records.uids) if declarations is not None else None,
        history_containing_null=declarations.containing_null if declarations is not None else None,
        history_null=declarations.null if declarations is not None else None,
        history_empty=declarations.empty if declarations is not None else None,
        history_nonempty=declarations.nonempty if declarations is not None else None,
        history_unknown=declarations.unknown if declarations is not None else None,
    )
    return tuple(rows), stats
