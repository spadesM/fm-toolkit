"""The season-statistics section: one record per player, walked end to end.

The section is one frame of the span region, which the directory does not list. It is found by
reading only the head of each frame there: the frames whose body starts with the section header
and the layout's schema are the candidates, and exactly one of them must walk end to end, from
its first record to the zero that ends the list and a footer ending the frame. Every record is
read by its own structure rather than searched for, so a byte out of place anywhere fails the
walk instead of shifting what later records read.

A record is keyed by the player's pindex plus one and holds a line per kind of match for the
player's own team, the same lines for each other team the player turned out for this season, and two
calendar-year lines. The walk keeps each line's offset; the lines are decoded only when rows are
built, which reads every field of a line with one struct.
"""

from __future__ import annotations

import dataclasses
import functools
import operator
import struct
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from fm26save._core._container import ContainerIndex, read_region_frame, region_frame_heads
from fm26save._core._errors import ReaderCheckError
from fm26save._core._layouts import SeasonStatsLayout, find_layout
from fm26save._core._reader_stats import SeasonStatsStats
from fm26save._core.models.clubs import Club
from fm26save._core.models.season_stats import PlayerSeasonStats, SeasonStatsKind
from fm26save._core.readers._common import SPAN_REGION, build_gap_padded_struct, layout_mismatch

SECTION_LABEL = "season statistics"
# The natural position that makes a player's line read its shared words as saves.
GOALKEEPER_POSITION = "GK"
_SECTION_MAGIC = b"\x03\x01tad."
_SECTION_HEADER_BYTES = len(_SECTION_MAGIC) + 2
_RECORD_PRESENT = 1
_LIST_END = 0
_SLOT_ABSENT = 0
_U16 = struct.Struct("<H")
_U32 = struct.Struct("<I")
# The competitions whose lines the overall line adds up.
_OVERALL_PARTS = (SeasonStatsKind.LEAGUE, SeasonStatsKind.CUP, SeasonStatsKind.CONTINENTAL)
_NO_CLUB: tuple[None, None, None, None] = (None, None, None, None)
# The fields the overall check adds up and the minutes check reads.
_SUMMARY_FIELDS = ("starts", "substitute_appearances", "minutes", "goals", "assists")


@dataclass(frozen=True, slots=True)
class RawSeasonRecord:
    """One record as walked: its key and the offset of each line, None for an absent slot.

    `other_teams` holds (team id, line offsets) for each other team the player turned out for.
    """

    key: int
    own_lines: tuple[int | None, ...]
    other_teams: tuple[tuple[int, tuple[int | None, ...]], ...]


@dataclass(frozen=True, slots=True)
class SeasonStatsWalk:
    """Every record of the section, in the order the save stores them."""

    records: tuple[RawSeasonRecord, ...]


@dataclass(frozen=True, slots=True)
class SeasonPlayer:
    """What a row needs of the player a record belongs to.

    `team_id` is the team the record's own lines are for, and `goalkeeper` whether GK is one of the
    natural positions, which decides how the words a keeper's line reuses are read.
    """

    uid: int
    name: str | None
    team_id: int | None
    goalkeeper: bool


@dataclass(frozen=True, slots=True)
class _LineReader:
    """One struct over a line's fields for one kind of player, and how its values become a row.

    `getter` pulls the row's statistic fields, in model order, out of the unpacked values with
    None appended, so a field this kind of player does not have reads that trailing None.
    `scaled` lists (row position, unit) for the fields stored in smaller units, and the average
    rating is filled in at `rating_position` from the rating sum and the rated appearances.
    """

    struct_object: struct.Struct
    start_offset: int
    getter: Callable[[tuple[object, ...]], tuple[object, ...]]
    scaled: tuple[tuple[int, int], ...]
    rating_position: int
    rating_sum_index: int
    rated_appearances_index: int


def find_season_stats_layout(build: str) -> SeasonStatsLayout:
    """Look up the season-statistics layout for a build, falling back to the known build."""
    return find_layout(SeasonStatsLayout, SPAN_REGION, None, build).layout


def _mismatch(file_name: str, detail: str) -> ReaderCheckError:
    return layout_mismatch(file_name, detail, SECTION_LABEL)


def _section_header(layout: SeasonStatsLayout) -> bytes:
    return _SECTION_MAGIC + _U16.pack(layout.section_schema)


def walk_season_stats(body: bytes, layout: SeasonStatsLayout, file_name: str) -> SeasonStatsWalk:
    """Walk every record of a section body, from its header to its footer.

    Raises:
        ReaderCheckError: The body does not start with the section header, a record or a slot
            does not start as the layout says, a count is above its maximum, or the walk does
            not end on the list terminator followed by exactly a footer's bytes.
    """
    if not body.startswith(_section_header(layout)):
        raise _mismatch(file_name, "the section does not start with its header")
    end = len(body)
    line_bytes = layout.line_bytes
    line_marker = layout.line_marker
    header_bytes = layout.header_bytes
    own_slot_count = layout.own_slots
    other_slot_count = layout.other_team_slots
    lead_bytes = layout.other_team_lead_bytes

    def read_slots(position: int, count: int) -> tuple[tuple[int | None, ...], int]:
        lines: list[int | None] = []
        for _ in range(count):
            if position >= end:
                raise _mismatch(file_name, "a record's slots run past the end of the section")
            if body[position] == _SLOT_ABSENT:
                lines.append(None)
                position += 1
            elif body.startswith(line_marker, position) and position + line_bytes <= end:
                lines.append(position)
                position += line_bytes
            else:
                raise _mismatch(
                    file_name,
                    f"the slot at byte {position:,} is neither absent nor a statistics line",
                )
        return tuple(lines), position

    def read_count(position: int, maximum: int, what: str) -> int:
        if position + _U32.size > end:
            raise _mismatch(file_name, f"a record's {what} count runs past the end of the section")
        count: int = _U32.unpack_from(body, position)[0]
        if count > maximum:
            raise _mismatch(file_name, f"a record at byte {position:,} counts {count:,} {what}")
        return count

    records: list[RawSeasonRecord] = []
    position = _SECTION_HEADER_BYTES
    while True:
        if position >= end:
            raise _mismatch(file_name, "the records run past the end of the section")
        marker = body[position]
        if marker == _LIST_END:
            break
        if marker != _RECORD_PRESENT or position + 1 + _U32.size + header_bytes > end:
            raise _mismatch(file_name, f"the record at byte {position:,} does not start as one")
        key: int = _U32.unpack_from(body, position + 1)[0]
        own_lines, position = read_slots(position + 1 + _U32.size + header_bytes, own_slot_count)
        position += layout.block_bytes
        other_count = read_count(position, layout.maximum_other_teams, "other teams")
        position += _U32.size
        other_teams: list[tuple[int, tuple[int | None, ...]]] = []
        for _ in range(other_count):
            team_at = position + lead_bytes
            if team_at + _U32.size > end:
                raise _mismatch(file_name, "a record's other team runs past the end of the section")
            team_id: int = _U32.unpack_from(body, team_at)[0]
            team_lines, position = read_slots(team_at + _U32.size, other_slot_count)
            other_teams.append((team_id, team_lines))
        item_count = read_count(position, layout.maximum_rating_items, "rating items")
        position += _U32.size + item_count * layout.rating_item_bytes
        if position >= end:
            raise _mismatch(file_name, "a record's form list runs past the end of the section")
        form_entries = body[position]
        if form_entries > layout.maximum_form_entries:
            raise _mismatch(
                file_name, f"the form list at byte {position:,} counts {form_entries} entries"
            )
        position += 1 + form_entries * layout.form_entry_bytes
        records.append(RawSeasonRecord(key, own_lines, tuple(other_teams)))
    footer_end = position + 1 + layout.footer_bytes
    if footer_end != end:
        raise _mismatch(
            file_name,
            f"the record list ends {end - footer_end:+,} bytes away from where its footer "
            "should end the section",
        )
    return SeasonStatsWalk(tuple(records))


def read_season_stats_section(
    container_index: ContainerIndex, layout: SeasonStatsLayout
) -> tuple[bytes, SeasonStatsWalk]:
    """Find the one span frame holding the section, and walk it.

    Raises:
        ReaderCheckError: No span frame starts with the section header, none of those that do
            walks end to end, or more than one does.
    """
    file_name = container_index.file_name
    header = _section_header(layout)
    candidates = [
        span
        for span, head in region_frame_heads(container_index, SPAN_REGION, len(header))
        if head == header
    ]
    if not candidates:
        raise _mismatch(file_name, "no frame of the span holds the season statistics section")
    walked: list[tuple[bytes, SeasonStatsWalk]] = []
    first_error: ReaderCheckError | None = None
    for span in candidates:
        body = read_region_frame(container_index, SPAN_REGION, span)
        try:
            walked.append((body, walk_season_stats(body, layout, file_name)))
        except ReaderCheckError as error:
            if first_error is None:
                first_error = error
    if not walked and first_error is not None:
        raise first_error
    if len(walked) > 1:
        raise _mismatch(file_name, f"{len(walked)} frames of the span each walk as the section")
    return walked[0]


# The statistic fields of a row, in model order: everything after the player and team fields.
_ROW_FIELDS = tuple(field.name for field in dataclasses.fields(PlayerSeasonStats))[
    len(("player_uid", "player_name", "kind", "team_id")) + len(_NO_CLUB) :
]


@functools.cache
def _line_readers(layout: SeasonStatsLayout) -> tuple[_LineReader, _LineReader]:
    """(outfield reader, goalkeeper reader), built on first use for each layout.

    Raises:
        ValueError: The layout's fields and the model's fields do not name the same statistics.
    """
    rated_name = _field_at(layout, layout.rated_appearances_offset)

    def reader(extra: tuple[tuple[str, int, str, int], ...]) -> _LineReader:
        specs = [(layout.rating_sum_offset, "H", "_rating_sum")]
        specs += [(offset, code, name) for name, offset, code, _ in (*layout.fields, *extra)]
        struct_object, start_offset, index_by_name = build_gap_padded_struct(specs)
        unit_by_name = {name: unit for name, _, _, unit in (*layout.fields, *extra)}
        absent_index = len(specs)
        shared_names = {name for name, *_ in (*layout.outfield_fields, *layout.goalkeeper_fields)}
        unknown = set(unit_by_name) - set(_ROW_FIELDS)
        missing = set(_ROW_FIELDS) - set(unit_by_name) - shared_names - {"average_rating"}
        if unknown or missing:
            raise ValueError(f"layout and model disagree: {sorted(unknown)} {sorted(missing)}")
        order = [index_by_name.get(name, absent_index) for name in _ROW_FIELDS]
        return _LineReader(
            struct_object=struct_object,
            start_offset=start_offset,
            getter=operator.itemgetter(*order),
            scaled=tuple(
                (position, unit_by_name[name])
                for position, name in enumerate(_ROW_FIELDS)
                if unit_by_name.get(name, 1) != 1
            ),
            rating_position=_ROW_FIELDS.index("average_rating"),
            rating_sum_index=index_by_name["_rating_sum"],
            rated_appearances_index=index_by_name[rated_name],
        )

    return reader(layout.outfield_fields), reader(layout.goalkeeper_fields)


def _field_at(layout: SeasonStatsLayout, offset: int) -> str:
    for name, field_offset, _, _ in layout.fields:
        if field_offset == offset:
            return name
    raise ValueError(f"no field of the layout sits at offset {offset}")


def _decode(body: bytes, offset: int, line_reader: _LineReader, rating_scale: int) -> list[object]:
    """A line's statistic fields, in model order."""
    values = line_reader.struct_object.unpack_from(body, offset + line_reader.start_offset)
    decoded = list(line_reader.getter((*values, None)))
    for position, unit in line_reader.scaled:
        decoded[position] = decoded[position] / unit  # pyright: ignore[reportOperatorIssue]
    rated = values[line_reader.rated_appearances_index]
    decoded[line_reader.rating_position] = (
        values[line_reader.rating_sum_index] / (rated * rating_scale) if rated else None
    )
    return decoded


def _club_fields(
    team_id: int | None,
    team_to_club: Mapping[int, tuple[int, int]],
    club_by_uid: Mapping[int, Club],
) -> tuple[int | None, str | None, str | None, int | None]:
    located = None if team_id is None else team_to_club.get(team_id)
    if located is None:
        return _NO_CLUB
    club_uid, team_slot = located
    club = club_by_uid.get(club_uid)
    if club is None:
        return club_uid, None, None, team_slot
    return club_uid, club.name, club.short_name, team_slot


def build_season_stats(
    walk: SeasonStatsWalk,
    body: bytes,
    players_by_pindex: Mapping[int, SeasonPlayer],
    team_to_club: Mapping[int, tuple[int, int]],
    club_by_uid: Mapping[int, Club],
    layout: SeasonStatsLayout,
) -> tuple[tuple[PlayerSeasonStats, ...], SeasonStatsStats]:
    """Build a row for every line of every record that belongs to a player, and count the checks.

    Rows come in the order the save stores the records; inside a record, the player's own
    lines come first in slot order, then each other team's. A record whose key names no player
    builds no row and is counted only in `SeasonStatsStats.records`, and a record whose key an
    earlier one had builds none either and is counted in `SeasonStatsStats.repeated_keys`, so a
    player's lines are never doubled.
    """
    outfield_reader, goalkeeper_reader = _line_readers(layout)
    slot_kinds = tuple(SeasonStatsKind(kind) for kind in layout.slot_kinds)
    overall_slot = slot_kinds.index(SeasonStatsKind.OVERALL)
    competition_slots = tuple(slot_kinds.index(kind) for kind in _OVERALL_PARTS)
    rating_scale = layout.rating_scale
    maximum_minutes = layout.maximum_minutes_per_appearance
    field_offsets = {name: offset for name, offset, _, _ in layout.fields}
    summary_struct, summary_start, summary_index = build_gap_padded_struct(
        [
            (field_offsets[name], code, name)
            for name, _, code, _ in layout.fields
            if name in _SUMMARY_FIELDS
        ]
    )
    summary_order = operator.itemgetter(*(summary_index[name] for name in _SUMMARY_FIELDS))
    minutes_at = _SUMMARY_FIELDS.index("minutes")
    starts_at = _SUMMARY_FIELDS.index("starts")
    substitutes_at = _SUMMARY_FIELDS.index("substitute_appearances")

    rows: list[PlayerSeasonStats] = []
    records_keyed = 0
    players_seen: set[int] = set()
    keys_seen: set[int] = set()
    repeated_keys = 0
    records_with_overall = 0
    overall_sums = 0
    lines = 0
    minutes_in_range = 0
    teams_resolved = 0

    def summary(offset: int) -> tuple[int, ...]:
        """The line's `_SUMMARY_FIELDS`, in that order."""
        return summary_order(summary_struct.unpack_from(body, offset + summary_start))

    for record in walk.records:
        all_lines = [*record.own_lines, *(line for _, team in record.other_teams for line in team)]
        for line in all_lines:
            if line is None:
                continue
            lines += 1
            values = summary(line)
            appearances = values[starts_at] + values[substitutes_at]
            minutes_in_range += values[minutes_at] <= maximum_minutes * appearances
        overall = record.own_lines[overall_slot]
        if overall is not None:
            records_with_overall += 1
            parts = [record.own_lines[slot] for slot in competition_slots]
            added = [0] * len(_SUMMARY_FIELDS)
            for part in parts:
                if part is not None:
                    added = [
                        total + value for total, value in zip(added, summary(part), strict=True)
                    ]
            overall_sums += tuple(added) == summary(overall)
        if record.key in keys_seen:
            repeated_keys += 1
            continue
        keys_seen.add(record.key)
        player = players_by_pindex.get(record.key - 1)
        if player is None:
            continue
        records_keyed += 1
        players_seen.add(record.key - 1)
        line_reader = goalkeeper_reader if player.goalkeeper else outfield_reader
        teams = [(player.team_id, record.own_lines), *record.other_teams]
        for team_id, team_lines in teams:
            club_uid, club_name, club_short_name, team_slot = _club_fields(
                team_id, team_to_club, club_by_uid
            )
            for slot, line in enumerate(team_lines):
                if line is None:
                    continue
                teams_resolved += club_uid is not None
                rows.append(
                    PlayerSeasonStats(
                        player.uid,
                        player.name,
                        slot_kinds[slot],
                        team_id,
                        club_uid,
                        club_name,
                        club_short_name,
                        team_slot,
                        *_decode(body, line, line_reader, rating_scale),  # pyright: ignore[reportArgumentType]
                    )
                )
    stats = SeasonStatsStats(
        records=len(walk.records),
        records_keyed_to_players=records_keyed,
        players=len(players_by_pindex),
        players_with_record=len(players_seen),
        records_with_overall=records_with_overall,
        overall_sums_competitions=overall_sums,
        lines=lines,
        minutes_in_range=minutes_in_range,
        rows=len(rows),
        teams_resolved=teams_resolved,
        repeated_keys=repeated_keys,
    )
    return tuple(rows), stats


def decode_season_line(
    body: bytes, offset: int, goalkeeper: bool, layout: SeasonStatsLayout
) -> list[object]:
    """Decode the shared statistic fields of a complete current-style line."""
    readers = _line_readers(layout)
    return _decode(body, offset, readers[int(goalkeeper)], layout.rating_scale)


def season_club_fields(
    team_id: int | None,
    team_to_club: Mapping[int, tuple[int, int]],
    club_by_uid: Mapping[int, Club],
) -> tuple[int | None, str | None, str | None, int | None]:
    """Resolve a statistics line's team without guessing a missing club."""
    return _club_fields(team_id, team_to_club, club_by_uid)
