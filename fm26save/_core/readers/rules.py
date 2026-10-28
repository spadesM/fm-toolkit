"""Competition rules and transfer windows, read from the span and from `game_db`.

**Competition rules come from the preamble blocks one span pass already collected**, so this
reader walks nothing of its own: it decodes, keys and counts what `SpanRecords.rules_blocks`
holds, and joins each block to a league table by where the save keeps it.

**A block's competition is its position in the span, not a field it stores.** The span
alternates rules blocks and table blocks, and the run of table blocks stored after a block is
the table that block's rules govern. Where that run holds exactly one league table's set of
clubs, and that table carries a competition the fixture calendar voted it, the row takes that
competition; otherwise it keeps none. On the saves measured that is about seven blocks in ten,
so 32% to 45% of rows carry no competition, and a run matching two tables at once carries none
rather than being resolved to either. The calendar corroborates the alignment: 0.74 to 0.78 of
a linked block's dated rounds fall on a date its competition plays a fixture on, against 0.55
to 0.58 when each block is linked to the run stored *before* it. It rests on the league-table vote, so a row's competition is exactly as strong as
`LeagueTable.competition_id` and no stronger.

**The tagged rules groups are not read.** The save's rules database does hold groups of squad
and financial rules -- a home-grown minimum, a maximum squad size, a salary cap, a wage-bill
percentage -- and a strict walk anchored on the wage-percentage tag does pin four of them per
save, identical in shape and count on every save measured. They are still not shipped,
for reasons that are measured rather than cautious:

- **nothing readable ties a group to a competition.** Seven routes were measured and recorded:
  counting groups against competitions, stages and tables; the run of tables after a group;
  the owning name record legacy used, whose ownership has no record boundary at all (the first
  range spans 5.2 MB); tagged competition references inside the owning range, which are small
  integers that hit some competition by chance about a third of the time; the four groups' own
  one-byte competition value, with the same objection; and the reverse lookup for the one
  division whose Rules screen was read in game, which finds dozens of tagged references and
  none of them under the division's own rule set. The positional link the preamble blocks use
  does not carry over, because a group is not stored beside a table;
- **the content is database content**, byte for byte the same on every save of one installed
  database, so it says nothing about any career;
- none of the four groups carries a string of any kind, so there is no group name to return;
- none carries the value tag the squad-size rule was supposed to be read through, so that rule
  is not in them at all;
- the wider population the groups were meant to come from is not bounded: of 324 candidates
  for the home-grown tag, 116 do not sit at a record boundary at all and the rest fall into
  three unrelated shapes;
- and no displayed in-game label pins the meaning of any value the groups hold, so naming one
  would rest on another tool's guess rather than on evidence.

Walking from the description marker, which is the obvious route, decodes nothing: on both
saves all 1,707 strict walks from it stop before reaching any rules tag.

Transfer windows are read from the tagged stream below.

The rules database is written as a tagged stream: a run of
`<4-byte tag, byte-reversed><01><type><value>` records. A transfer window is one such run,
opening with its start-date sub-list and ending at its closing-time value.

**Why the closing time is what recognises a window.** The date tags a window uses are shared
by many kinds of record in this stream. On the saves measured over a thousand start-date
sub-lists carry a complete, in-range date pair and only 54 of them also carry a closing time,
so accepting on
the dates alone would return every dated record the rules database holds. Acceptance is
structural throughout: the record carries no description of its own, and the description
strings elsewhere in the stream belong to other records, so nothing here reads text.

The walk is the strict one in `fmsave._scan`, which stops at the first byte that is not a
record rather than hunting for the next one. That is what keeps a layout that has moved
visibly empty instead of quietly short.

**The rules database stores its windows more than once.** Every window record the stream holds
is returned, which is more records than there are distinct windows: on the saves measured 54
records and 22 distinct windows. The repeats are neither a decode fault nor dropped here, since
dropping them would hide a change in what a save stores behind a number that never moved.
`fmsave.models.rules.TransferWindow` sets out what a repeated row means and what a caller can
do about it.
"""

from __future__ import annotations

import datetime
from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from collections.abc import Set as AbstractSet

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import TaggedStreamLayout, TransferWindowLayout, find_layout
from fm26save._core._reader_stats import RulesStats, TransferWindowStats
from fm26save._core._scan import iter_tagged_values
from fm26save._core.models.fixtures import Fixture
from fm26save._core.models.league_tables import LeagueTable
from fm26save._core.models.rules import CompetitionRules, RulesBlockKind, RulesRound, TransferWindow
from fm26save._core.readers._common import GAME_DB_SECTION
from fm26save._core.readers.competitions import CompetitionIndex
from fm26save._core.readers.span import RawRulesBlock, RawTableBlock, SpanRecords

CLOSE_TIME_KEY = "close_time"
WINDOW_TYPE_KEY = "window_type"
PROMOTION_BYTE2_KEY = CompetitionRules.UNKNOWN_KEYS[0]
TIE_BREAK_KEYS = CompetitionRules.UNKNOWN_KEYS[1:]
ROUND_KIND_KEY, ROUND_B5_KEY = RulesRound.UNKNOWN_KEYS


def _preamble_unknown(block: RawRulesBlock) -> FrozenMapping[str, int]:
    """The quad's unidentified byte and the tie-break codes, in the order the block lists them.

    The tie-break codes are paired with the declared keys rather than numbered from the list,
    so a block carrying more codes than there are keys can never produce a key the record does
    not declare. No displayed label names a tie-break code, so they ship as raw numbers.
    """
    unknown: dict[str, int] = {}
    if block.promotion_byte2 is not None:
        unknown[PROMOTION_BYTE2_KEY] = block.promotion_byte2
    for key, code in zip(TIE_BREAK_KEYS, block.tie_breaks, strict=False):
        unknown[key] = code
    return FrozenMapping(unknown)


def _rounds_of(block: RawRulesBlock) -> tuple[RulesRound, ...]:
    return tuple(
        RulesRound(
            number=raw_round.number,
            date=raw_round.date,
            match_count=raw_round.match_count,
            unknown=FrozenMapping({ROUND_KIND_KEY: raw_round.kind, ROUND_B5_KEY: raw_round.b5}),
        )
        for raw_round in block.rounds
    )


def _table_run_after_each_block(
    blocks: Sequence[RawRulesBlock], table_blocks: Sequence[RawTableBlock]
) -> tuple[frozenset[int], ...]:
    """The set of clubs each block's following run of table blocks holds, one set per block.

    A block's run is the table blocks the span stores between it and the next preamble block,
    and everything to the end of the span for the last block. Both sequences are sorted here
    rather than assumed sorted: the run is defined by span position and nothing else promises
    the span pass returns its finds in that order.

    The result is in the order `blocks` came in, not in span order, so a row keeps the run of
    the block it was built from however the span pass ordered its finds.
    """
    boundaries = sorted(block.span_offset for block in blocks)
    ordered = sorted(table_blocks, key=lambda table_block: table_block.span_offset)
    offsets = [table_block.span_offset for table_block in ordered]
    run_by_offset: dict[int, frozenset[int]] = {}
    for position, block_offset in enumerate(boundaries):
        start = bisect_right(offsets, block_offset)
        stop = (
            bisect_left(offsets, boundaries[position + 1])
            if position + 1 < len(boundaries)
            else len(offsets)
        )
        run_by_offset[block_offset] = frozenset(
            table_block.team_id for table_block in ordered[start:stop]
        )
    return tuple(run_by_offset[block.span_offset] for block in blocks)


def _tables_by_club_set(
    league_tables: Sequence[LeagueTable],
) -> dict[frozenset[int], list[LeagueTable]]:
    """Every table keyed by the set of clubs it holds, so an ambiguous set is visible as one."""
    by_club_set: dict[frozenset[int], list[LeagueTable]] = {}
    for table in league_tables:
        by_club_set.setdefault(frozenset(row.team_id for row in table.rows), []).append(table)
    return by_club_set


def _competition_fixture_dates(fixtures: Sequence[Fixture]) -> dict[int, set[datetime.date]]:
    """The dates each competition plays a fixture on, which is what corroborates a link."""
    dates_by_competition: dict[int, set[datetime.date]] = {}
    for fixture in fixtures:
        competition_id = fixture.competition_id
        fixture_date = fixture.date
        if competition_id is None or fixture_date is None:
            continue
        dates_by_competition.setdefault(competition_id, set()).add(fixture_date)
    return dates_by_competition


def _round_corroboration(
    block: RawRulesBlock, table: LeagueTable, competition_dates: AbstractSet[datetime.date]
) -> tuple[int, int, bool]:
    """One linked block's dated rounds, how many the competition plays on, and its shape.

    The dates are what the link is checked by. The shape -- a round count of `2(n - 1)` or
    `n - 1` for a table of `n` clubs -- is counted beside them and **not** checked: it holds on
    0.71 to 0.77 of linked blocks and on 0.56 to 0.62 when each block is linked to the run
    stored before it instead, so a floor that both fails that misalignment and keeps a fifth of
    its own width clear of the lowest linked value has to sit between 0.62 and 0.64. A window
    two points wide is not one to rest a gate on given the saves tested, and the round dates
    judge the same alignment with room to spare.
    """
    dated_rounds = [raw_round.date for raw_round in block.rounds if raw_round.date is not None]
    in_calendar = sum(1 for round_date in dated_rounds if round_date in competition_dates)
    club_count = table.club_count
    shaped = bool(block.rounds) and len(block.rounds) in (2 * (club_count - 1), club_count - 1)
    return len(dated_rounds), in_calendar, shaped


def build_competition_rules(
    span_records: SpanRecords,
    league_tables: Sequence[LeagueTable],
    fixtures: Sequence[Fixture],
    competition_index: CompetitionIndex,
) -> tuple[tuple[CompetitionRules, ...], RulesStats]:
    """Key the span's rules preamble blocks into rows, in the order the span stores them.

    A row's competition comes from **where the save keeps the block**, not from anything the
    block stores. The span alternates rules blocks and table blocks, and the run of table
    blocks stored after a block is the table that block's rules govern: on the saves measured
    about seven blocks in ten have such a run, nearly all of those runs hold exactly one league
    table's set of clubs, and nearly all of those tables carry a competition the fixture
    calendar voted them. The rest keep `competition_id` empty, which is
    32% to 45% of rows, and a run matching two tables at once is turned away rather than
    resolved to either.

    That is a position in a file rather than a stored key, so it is corroborated: 0.74 to 0.78
    of a linked block's dated rounds fall on a date its competition plays a fixture
    on, against 0.55 to 0.58 when each block is linked to the run stored *before* it
    instead. `rules_link_round_dates` is the check on that. The competition itself is a vote on
    the calendar rather than a stored value, so a row's competition is no stronger than
    `LeagueTable.competition_id`, and both are unconfirmed.

    A block whose promotion quad was not written twice keeps its lists and its calendar and
    leaves the four quad fields empty, rather than being dropped.
    """
    blocks = span_records.rules_blocks
    runs = _table_run_after_each_block(blocks, span_records.table_blocks)
    tables_by_club_set = _tables_by_club_set(league_tables)
    dates_by_competition = _competition_fixture_dates(fixtures)
    name_for = competition_index.name_for

    rows: list[CompetitionRules] = []
    blocks_with_run = 0
    blocks_linked = 0
    blocks_linked_with_competition = 0
    linked_rounds = 0
    linked_rounds_in_calendar = 0
    linked_round_shape = 0
    for block, run in zip(blocks, runs, strict=True):
        competition_id: int | None = None
        if run:
            blocks_with_run += 1
            linked = tables_by_club_set.get(run, ())
            if len(linked) == 1:
                blocks_linked += 1
                linked_table = linked[0]
                competition_id = linked_table.competition_id
                if competition_id is not None:
                    blocks_linked_with_competition += 1
                    dated, in_calendar, shaped = _round_corroboration(
                        block, linked_table, dates_by_competition.get(competition_id, frozenset())
                    )
                    linked_rounds += dated
                    linked_rounds_in_calendar += in_calendar
                    linked_round_shape += int(shaped)
        rows.append(
            CompetitionRules(
                kind=RulesBlockKind.PREAMBLE,
                competition_id=competition_id,
                competition_name=name_for(competition_id),
                fixtures_per_club=len(block.rounds) or None,
                promotion_places=block.promotion_places,
                playoff_places=block.playoff_places,
                relegation_places=block.relegation_places,
                prize_money=block.prize_money,
                rounds=_rounds_of(block),
                unknown=_preamble_unknown(block),
            )
        )
    stats = RulesStats(
        markers=span_records.rules_markers,
        blocks=len(blocks),
        fully_parsed=sum(1 for block in blocks if block.fully_parsed),
        quad_doubled=sum(1 for block in blocks if block.promotion_places is not None),
        rows=len(rows),
        blocks_with_run=blocks_with_run,
        blocks_linked=blocks_linked,
        blocks_linked_with_competition=blocks_linked_with_competition,
        linked_rounds=linked_rounds,
        linked_rounds_in_calendar=linked_rounds_in_calendar,
        linked_round_shape=linked_round_shape,
    )
    return tuple(rows), stats


def find_transfer_window_layouts(
    game_db_schema: int | None, build: str
) -> tuple[TaggedStreamLayout, TransferWindowLayout]:
    """The tagged-stream and transfer-window layouts for a `game_db` schema, build as fallback."""
    return (
        find_layout(TaggedStreamLayout, GAME_DB_SECTION, game_db_schema, build).layout,
        find_layout(TransferWindowLayout, GAME_DB_SECTION, game_db_schema, build).layout,
    )


def _season_dates(
    group: dict[str, int], layout: TransferWindowLayout
) -> tuple[int, int, int] | None:
    """(day, month, season year offset) for one date sub-list, or None when it does not hold."""
    day = group.get(layout.day_tag)
    month = group.get(layout.month_tag)
    year = group.get(layout.year_tag)
    if day is None or month is None or year is None:
        return None
    lowest_day, highest_day = layout.day_range
    lowest_month, highest_month = layout.month_range
    lowest_year, highest_year = layout.year_range
    if not lowest_day <= day <= highest_day:
        return None
    if not lowest_month <= month <= highest_month:
        return None
    if not lowest_year <= year <= highest_year:
        return None
    return day, month, year - layout.season_year_base


def _decode_window(
    game_db: bytes,
    marker_offset: int,
    tagged_layout: TaggedStreamLayout,
    layout: TransferWindowLayout,
) -> tuple[TransferWindow | None, bool]:
    """Decode one candidate: the window when it holds, and whether a closing time was found.

    A sub-list holds more members than its three dates, so nothing is counted down: the date
    tags seen while a sub-list is open belong to it, and the next sub-list or the closing time
    closes it.
    """
    scan_end = min(marker_offset + layout.window_scan_bytes, len(game_db))
    groups: dict[str, dict[str, int]] = {}
    open_group: dict[str, int] | None = None
    close_time: int | None = None
    window_type: int | None = None
    date_tags = (layout.day_tag, layout.month_tag, layout.year_tag)
    for tagged in iter_tagged_values(game_db, marker_offset, scan_end, tagged_layout):
        tag = tagged.tag
        if tagged.kind == tagged_layout.list_type and tag in (layout.start_tag, layout.end_tag):
            open_group = {}
            groups[tag] = open_group
            continue
        value = tagged.value
        if not isinstance(value, int):
            continue
        if tag == layout.window_type_tag:
            window_type = value
        elif tag == layout.close_time_tag:
            close_time = value
            break
        elif open_group is not None and tag in date_tags:
            open_group[tag] = value
    if close_time is None:
        return None, False
    start_group = groups.get(layout.start_tag)
    end_group = groups.get(layout.end_tag)
    if start_group is None or end_group is None:
        return None, True
    opens = _season_dates(start_group, layout)
    closes = _season_dates(end_group, layout)
    if opens is None or closes is None:
        return None, True
    unknown = {CLOSE_TIME_KEY: close_time}
    if window_type is not None:
        unknown[WINDOW_TYPE_KEY] = window_type
    return (
        TransferWindow(
            start_day=opens[0],
            start_month=opens[1],
            start_season_year_offset=opens[2],
            end_day=closes[0],
            end_month=closes[1],
            end_season_year_offset=closes[2],
            unknown=FrozenMapping(unknown),
        ),
        True,
    )


def read_transfer_windows(
    game_db: bytes, tagged_layout: TaggedStreamLayout, layout: TransferWindowLayout
) -> tuple[tuple[TransferWindow, ...], TransferWindowStats]:
    """Every transfer window the rules database holds, in the order `game_db` stores them.

    Each occurrence of the start-date sub-list is a candidate; the walk from it decides. A
    candidate with no closing time is not a window and is not counted as a failure, because
    most start-date sub-lists in this stream belong to other kinds of record.
    """
    marker = layout.marker
    windows: list[TransferWindow] = []
    marker_count = 0
    incomplete = 0
    marker_offset = game_db.find(marker)
    while marker_offset >= 0:
        marker_count += 1
        window, carried_close_time = _decode_window(game_db, marker_offset, tagged_layout, layout)
        if window is not None:
            windows.append(window)
        elif carried_close_time:
            incomplete += 1
        marker_offset = game_db.find(marker, marker_offset + 1)
    stats = TransferWindowStats(markers=marker_count, windows=len(windows), incomplete=incomplete)
    return tuple(windows), stats
