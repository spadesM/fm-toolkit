"""The Save object returned by fmsave.open."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from types import TracebackType
from typing import NamedTuple, Self, cast

from fm26save._core import _checks
from fm26save._core._checks import GateResult, ReaderCheck
from fm26save._core._container import ContainerIndex, read_index, read_section
from fm26save._core._context import SaveContext, closed_save_error
from fm26save._core._errors import ReaderCheckError
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import (
    ContractLayout,
    FixtureCalendarLayout,
    GateBounds,
    LeagueTableLayout,
    PersonBlockLayout,
    StadiumTableLayout,
    StageResultLayout,
    SuspensionLayout,
    find_layout,
)
from fm26save._core._reader_stats import ResultStats, TacticStats
from fm26save._core._version import read_save_info
from fm26save._core.models.affiliates import AffiliateGroup
from fm26save._core.models.clubs import Club
from fm26save._core.models.competitions import Competition, Stage
from fm26save._core.models.contracts import Contract
from fm26save._core.models.facilities import ClubFacilities
from fm26save._core.models.finances import FinanceMonth, Sponsorship
from fm26save._core.models.fixtures import Fixture
from fm26save._core.models.injuries import InjuryRecord, InjuryType
from fm26save._core.models.jobs import JobVacancy
from fm26save._core.models.league_tables import LeagueTable
from fm26save._core.models.managed import ManagedClub
from fm26save._core.models.matches import PlayerMatchStats
from fm26save._core.models.meta import SaveInfo
from fm26save._core.models.players import Player
from fm26save._core.models.rules import CompetitionRules, TransferWindow
from fm26save._core.models.season_history import PlayerSeasonHistory
from fm26save._core.models.season_stats import PlayerSeasonStats
from fm26save._core.models.stadiums import Stadium
from fm26save._core.models.staff import Staff, StaffList
from fm26save._core.models.suspensions import Suspension
from fm26save._core.models.tactics import SetPieceRoutine, Tactic
from fm26save._core.models.training import MentoringGroup, TeamTraining
from fm26save._core.name_maps import (
    _EMPTY_COMPETITION_NAMES,  # pyright: ignore[reportPrivateUsage]
    _normalized_competition_names,  # pyright: ignore[reportPrivateUsage]
)
from fm26save._core.readers._common import (
    FEEDER_SECTION,
    GAME_DB_SECTION,
    HUMANS_SECTION,
    INJURY_MANAGER_SECTION,
    JOB_CENTRE_SECTION,
    SAVE_SUMMARY_SECTION,
    SPAN_REGION,
    TACTICS_SECTION,
    TRAINING_SECTION,
)
from fm26save._core.readers.affiliates import (
    build_affiliate_groups,
    find_affiliate_layout,
    walk_affiliate_groups,
)
from fm26save._core.readers.facilities import find_facility_layout, read_club_facilities
from fm26save._core.readers.finances import find_finance_layouts, read_club_finances
from fm26save._core.readers.fixtures import build_fixtures_with_offsets
from fm26save._core.readers.injuries import (
    build_injury_records,
    find_injury_manager_layout,
    find_injury_type_layout,
    read_injury_types,
    walk_injury_manager,
)
from fm26save._core.readers.jobs import find_job_centre_layout, read_job_vacancies
from fm26save._core.readers.league_tables import build_league_tables
from fm26save._core.readers.managed import (
    find_managed_club_layouts,
    first_human_selector,
    resolve_managed_clubs,
)
from fm26save._core.readers.match_summaries import (
    MatchSummaryScores,
    find_match_summary_layout,
    locate_match_summary_scores,
)
from fm26save._core.readers.matches import (
    build_player_match_stats,
    find_match_record_layout,
    locate_match_records,
)
from fm26save._core.readers.player_scan import window_end
from fm26save._core.readers.players import build_player_decoder, collect_player_stats
from fm26save._core.readers.results import (
    apply_results,
    calendar_dates,
    find_result_layout,
    locate_stage_results,
    result_in_scope,
)
from fm26save._core.readers.rules import (
    build_competition_rules,
    find_transfer_window_layouts,
    read_transfer_windows,
)
from fm26save._core.readers.season_history import (
    ARCHIVE_SECTION,
    build_history,
    find_history_layout,
    history_selector,
    read_history_index,
)
from fm26save._core.readers.season_stats import (
    GOALKEEPER_POSITION,
    SeasonPlayer,
    build_season_stats,
    find_season_stats_layout,
    read_season_stats_section,
)
from fm26save._core.readers.span import SPAN_RECORDS_CACHE_KEY, SpanRecords
from fm26save._core.readers.stadiums import (
    StadiumIndex,
    build_stadiums,
    find_stadium_layout,
    stadium_table_stats,
)
from fm26save._core.readers.staff import find_staff_layouts, read_staff
from fm26save._core.readers.stages import StageIndex, named_stages
from fm26save._core.readers.suspensions import (
    SuspensionEntry,
    locate_suspensions,
    named_entries,
    suspension_rows,
    suspension_stats,
)
from fm26save._core.readers.tactics import (
    build_tactic_tables,
    find_tactics_layout,
    read_tactics_header,
    walk_tactic_blocks,
)
from fm26save._core.readers.training import (
    build_training_tables,
    find_training_layout,
    locate_schedule_library,
    unmanaged_training_stats,
    walk_training_blocks,
)
from fm26save._core.table import Table

CLUBS_TABLE_CACHE_KEY = "table:clubs"
PLAYERS_TABLE_CACHE_KEY = "table:players"
CONTRACTS_TABLE_CACHE_KEY = "table:contracts"
SUSPENSIONS_TABLE_CACHE_KEY = "table:suspensions"
MANAGED_CLUBS_TABLE_CACHE_KEY = "table:managed_clubs"
STAGES_TABLE_CACHE_KEY = "table:stages"
COMPETITIONS_TABLE_CACHE_KEY = "table:competitions"
FIXTURES_TABLE_CACHE_KEY = "table:fixtures"
TRANSFER_WINDOWS_TABLE_CACHE_KEY = "table:transfer_windows"
LEAGUE_TABLES_TABLE_CACHE_KEY = "table:league_tables"
COMPETITION_RULES_TABLE_CACHE_KEY = "table:competition_rules"
PLAYER_MATCH_STATS_TABLE_CACHE_KEY = "table:player_match_stats"
PLAYER_SEASON_HISTORY_TABLE_CACHE_KEY = "table:player_season_history"
HISTORY_SELECTORS_CACHE_KEY = "player_history_selectors"
PLAYER_SEASON_STATS_TABLE_CACHE_KEY = "table:player_season_stats"
INJURY_TYPES_TABLE_CACHE_KEY = "table:injury_types"
INJURIES_TABLE_CACHE_KEY = "table:injuries"
FINANCES_TABLE_CACHE_KEY = "table:finances"
SPONSORSHIPS_TABLE_CACHE_KEY = "table:sponsorships"
FACILITIES_TABLE_CACHE_KEY = "table:facilities"
AFFILIATES_TABLE_CACHE_KEY = "table:affiliates"
JOB_VACANCIES_TABLE_CACHE_KEY = "table:job_vacancies"
STADIUMS_TABLE_CACHE_KEY = "table:stadiums"
STAFF_TABLE_CACHE_KEY = "table:staff"
STAFF_LISTS_TABLE_CACHE_KEY = "table:staff_lists"
TACTICS_TABLE_CACHE_KEY = "table:tactics"
SET_PIECES_TABLE_CACHE_KEY = "table:set_pieces"
TRAINING_TABLE_CACHE_KEY = "table:training"
MENTORING_TABLE_CACHE_KEY = "table:mentoring"

# What each shared decode is kept under. While nothing is stored there the decode has not
# finished, which is what tells a failed pass from a failed reader of a pass that ran.
_SHARED_PASS_CACHE_KEYS: Mapping[str, str] = {
    _checks.PLAYER_PASS: PLAYERS_TABLE_CACHE_KEY,
    _checks.SPAN_PASS: SPAN_RECORDS_CACHE_KEY,
    _checks.FINANCE_PASS: FINANCES_TABLE_CACHE_KEY,
    _checks.STAFF_PASS: STAFF_TABLE_CACHE_KEY,
    _checks.TACTICS_PASS: TACTICS_TABLE_CACHE_KEY,
    _checks.TRAINING_PASS: TRAINING_TABLE_CACHE_KEY,
}


class _FinanceTables(NamedTuple):
    """The two tables one decode pass over the club records builds, and their _checks."""

    finances: Table[FinanceMonth]
    sponsorships: Table[Sponsorship]
    reader_checks: tuple[ReaderCheck, ...]


# What a save with no managed club counts: a manager between jobs has no team block at all, so
# every tactic check stands aside rather than judging an empty result.
_EMPTY_TACTIC_STATS = TacticStats(
    managed_club_exists=False,
    club_team_count=0,
    header_blocks=0,
    stored_blocks=0,
    stored_club_blocks=0,
    blocks_found=0,
    selector_matches=False,
    selection_selectors=0,
    selection_selectors_resolved=0,
    selection_selectors_at_club=0,
    tactic_blocks=0,
    tactic_blocks_count_matching=0,
    stored_tactics=0,
    preset_tactics=0,
    slot_walks_complete=0,
    oop_index_permutations=0,
    routine_blocks=0,
    routine_blocks_complete=0,
    routines=0,
    named_routines=0,
)


class _TacticTables(NamedTuple):
    """The two tables one walk over the manager's team blocks builds, and their _checks."""

    tactics: Table[Tactic]
    set_pieces: Table[SetPieceRoutine]
    reader_checks: tuple[ReaderCheck, ...]


class _StaffTables(NamedTuple):
    """The two tables one decode pass over the club lists and the staff objects builds."""

    staff: Table[Staff]
    staff_lists: Table[StaffList]
    reader_checks: tuple[ReaderCheck, ...]


class _TrainingTables(NamedTuple):
    """The two tables one walk over the training section builds, and their _checks."""

    training: Table[TeamTraining]
    mentoring: Table[MentoringGroup]
    reader_checks: tuple[ReaderCheck, ...]


class _PlayerTables(NamedTuple):
    """The three tables one decode pass over the player records builds, and their _checks."""

    players: Table[Player]
    contracts: Table[Contract]
    suspensions: Table[Suspension]
    reader_checks: tuple[ReaderCheck, ...]


def _check_cache_key(reader_name: str) -> str:
    return f"check:{reader_name}"


def _returning[ValueT](value: ValueT) -> Callable[[], ValueT]:
    return lambda: value


class Save:
    """A Football Manager 26 save opened for reading.

    Opening reads only the header, the directory and the save metadata; the file is
    not kept open. Each reader reopens the file, checks that it has not changed since
    it was opened, and reads only the parts it needs.

    Every reader measures what it decoded against the bounds its checks carry. A failed check
    warns with `ReaderCheckWarning` and the reader hands its table back; a save opened with
    `strict=True` raises `ReaderCheckError` instead. A structural failure, where the decode
    has no table to hand back, raises either way. `fmsave.validate_save` reports every check
    of every reader without raising or warning.

    A Save is not thread-safe: use one Save per thread. Records and tables it returns
    are immutable, safe to share, and keep working after the Save is closed.
    """

    __slots__ = ("_container_index", "_context", "_info", "_strict", "_warned_readers")

    def __init__(
        self,
        container_index: ContainerIndex,
        info: SaveInfo,
        *,
        strict: bool = False,
        competition_names: FrozenMapping[int, str] = _EMPTY_COMPETITION_NAMES,
    ) -> None:
        self._container_index = container_index
        self._info = info
        # Settled when the save is opened and never changed afterwards, which is what makes a
        # failed check safe to cache: the result cache remembers a build that raised the
        # library's own error and raises it again without rebuilding, so a reader that raised
        # for a failed check must raise for every later call on this save. Nothing may switch
        # this on or off around a call. `validate_save` used to, and a caller who ran it on a
        # save opened the ordinary way was left with readers that raised ever after.
        self._strict = strict
        # The readers already warned about, so a save warns at most once for each of them.
        self._warned_readers: set[str] = set()
        self._context = SaveContext(container_index, info, competition_names=competition_names)

    @property
    def info(self) -> SaveInfo:
        """Game, build, database version, in-game date and section schemas."""
        return self._info

    @property
    def closed(self) -> bool:
        """Whether the save has been closed. Readers raise SaveClosedError once it is."""
        return self._context.closed

    def clubs(self) -> Table[Club]:
        """Every club in the save's game database, in club index order.

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears
                in two records, or a team id is listed twice (by one club or by two).

        Warns:
            ReaderCheckWarning: On a full-size save, the club records fall outside the checks'
                bounds. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(CLUBS_TABLE_CACHE_KEY, self._read_clubs)

    def players(self) -> Table[Player]:
        """Every player in the save's game database, in record offset order.

        Person fields (name, birth date, nationality, personality, traits and the rest) are filled
        in from each player's person block, or stay None or empty when no block validates.
        The table is read on the first call to `players()`, `contracts()` or `suspensions()`,
        from one decode pass; later calls to any of them return the same tables. When a check
        of that pass fails, none of the three tables is kept, so each of them raises.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written, a player's relation
                header or entry list runs past its record window, or a legal name is not
                valid UTF-8.
            ReaderCheckError: No club record is accepted, a club uid or club index appears
                in two records, a team id is listed twice (by one club or by two), no player
                records were found, two player records share a uid, or the save's in-game
                date is unreadable. With a name map, also anything the competition reader
                raises, since the pass names each ban's competition from that table.

        Warns:
            ReaderCheckWarning: On a full-size save, the players, contracts or suspensions
                decoded fall outside the checks' bounds, or, with a name map, the competition
                table does. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(PLAYERS_TABLE_CACHE_KEY, self._players_table_entry_point)

    def contracts(self) -> Table[Contract]:
        """Every player's contract in the save's game database, in player order.

        Only players whose contract is not None appear. The table is read on the first
        call to `players()`, `contracts()` or `suspensions()`, from one decode pass; later
        calls to any of them return the same tables. When a check of that pass fails, none
        of the three tables is kept, so each of them raises.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written, a player's relation
                header or entry list runs past its record window, or a legal name is not
                valid UTF-8.
            ReaderCheckError: No club record is accepted, a club uid or club index appears
                in two records, a team id is listed twice (by one club or by two), no player
                records were found, two player records share a uid, or the save's in-game
                date is unreadable. With a name map, also anything the competition reader
                raises, since the pass names each ban's competition from that table.

        Warns:
            ReaderCheckWarning: On a full-size save, the players, contracts or suspensions
                decoded fall outside the checks' bounds, or, with a name map, the competition
                table does. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(CONTRACTS_TABLE_CACHE_KEY, self._contracts_table_entry_point)

    def suspensions(self) -> Table[Suspension]:
        """Every unserved suspension in the save's game database, in player order.

        Every unserved ban the save holds is listed, including bans the game no longer
        displays. Each player's
        suspensions keep the order the save stores them in, and each row carries the club the
        player belongs to, which for a player registered with a team another club controls is
        that controlling club. The table is read on the first call to
        `players()`, `contracts()` or `suspensions()`, from one decode pass; later calls to
        any of them return the same tables. When a check of that pass fails, none of the
        three tables is kept, so each of them raises.

        A ban covering one competition carries `competition_id` in the stage id space, which
        joins `stages()`, `competitions()`, `fixtures()`, `league_tables()` and
        `player_match_stats()`; a nation-wide ban carries `nation_id` instead, and `scope`
        says which. `competition_name` is None unless the save was opened with a name map,
        and stays None for a competition the game itself created during the career, whose
        database id no name source outside the save carries.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written, a player's relation
                header or entry list runs past its record window, or a legal name is not
                valid UTF-8.
            ReaderCheckError: No club record is accepted, a club uid or club index appears
                in two records, a team id is listed twice (by one club or by two), no player
                records were found, two player records share a uid, or the save's in-game
                date is unreadable. With a name map, also anything the competition reader
                raises, since every competition name a ban carries comes from that table.

        Warns:
            ReaderCheckWarning: On a full-size save, the players, contracts or suspensions
                decoded fall outside the checks' bounds, or, with a name map, the competition
                table does. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(SUSPENSIONS_TABLE_CACHE_KEY, self._suspensions_table_entry_point)

    def managed_clubs(self) -> Table[ManagedClub]:
        """The club run by the save's first human manager.

        An empty table means no managed club was found: the save has no human manager, or
        the manager has no current club, for example while between jobs. The link from a
        human manager to a club is proven only on saves with a single human manager; on a
        save with several, only the first is listed. The club comes from the manager's
        current contract and is checked against the save summary, which also stores the
        manager's name. The table is read on the first call; later calls return the same
        table. It does not decode players.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears in
                two records, a team id is listed twice, the save's in-game date is unreadable,
                the contract and the save summary link the manager to different clubs, or,
                with no current contract, the save summary links the manager to more than
                one club.
        """
        context = self._context
        return context.cached(MANAGED_CLUBS_TABLE_CACHE_KEY, self._read_managed_clubs)

    def stages(self) -> Table[Stage]:
        """Every stage of every competition, in the order the save's stage table stores them.

        A stage is one part of a competition: a league season is one stage, a cup round is one,
        and each leg of a two-legged tie is its own stage carrying the same round. Stage ids are
        what fixtures, league-table groups and per-match records join through. No save stores a
        competition name, so `competition_name` is None unless the save was opened with a name
        map, and then it is filled in for the competitions that map names. The table is read on
        the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No stage table was found in the tail of the game database, or a
                stage id appears in two rows. With a name map the competition reader runs
                first, so anything it raises is raised here too, since a stage's competition
                name is read out of that table.

        Warns:
            ReaderCheckWarning: On a full-size save, the stage table falls outside the checks'
                bounds, or, with a name map, the competition table does. A save opened with
                strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(STAGES_TABLE_CACHE_KEY, self._read_stages)

    def competitions(self) -> Table[Competition]:
        """Every competition the save's stage table names, in ascending competition id.

        Each row carries the ids of its stages and, for about nine competitions in ten, the
        competition's id in the game's own editor database, which is the same value on every
        save and is what an external name source is keyed on. The save stores no competition
        names, so `name` is None on every row until a name map is supplied.
        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No stage table was found in the tail of the game database, or a
                stage id appears in two rows.

        Warns:
            ReaderCheckWarning: On a full-size save, fewer competitions were found than the
                checks allow. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(COMPETITIONS_TABLE_CACHE_KEY, self._read_competitions)

    def fixtures(self) -> Table[Fixture]:
        """Matches recovered from the fixture calendar, in date and kick-off order.

        The save holds several copies of the calendar; only the largest is returned, so the
        block of template matches every save carries is left out. Each row joins to its
        competition through its stage, and to a club through each team id; an id the save does
        not resolve leaves its fields empty rather than being guessed.

        `home_goals` and `away_goals` carry unambiguous decoded scores; coverage varies
        between saves. A played match with empty goals has no unambiguous decoded
        result. This does not establish whether the save retained its score, and does not mean
        the match finished goalless.

        `stadium_uid` names the ground each match is played at, which comes from the stadium
        table: this reader therefore needs that table and raises when the game database holds
        none.

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears in
                two records, a team id is listed twice, no stage table was found in the tail of
                the game database, a stage id appears in two rows, no stadium table was found,
                or the save's in-game date is unreadable. With a competition name map, the
                competition reader runs first and raises here too, so no row is named from a
                table that could not be read.

        Warns:
            ReaderCheckWarning: On a full-size span, the calendar or the scores joined onto it
                fall outside the checks' bounds. The stadium table's checks run here as well,
                and with a name map the competition table's, since a row carries a ground and a
                name from each. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(FIXTURES_TABLE_CACHE_KEY, self._read_fixtures)

    def _read_fixtures(self) -> Table[Fixture]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        layout = find_layout(FixtureCalendarLayout, SPAN_REGION, None, save_info.build).layout
        # One game_db borrow covers all three indexes the joins go through, so a cold call
        # decompresses that section once rather than once per index. The span is streamed after
        # the borrow ends, so the two large regions are never held in memory together.
        with context.section(GAME_DB_SECTION) as game_db:
            club_index = context.club_index()
            # With a name map the competitions are read first, checks and all. Every
            # competition name a fixture row carries comes out of the competition index, so
            # that index must have passed its own checks before a name of its leaves this
            # reader: a build that mis-paired entity ids with database ids would otherwise put
            # another competition's name on every one of a hundred thousand fixture rows and
            # raise nothing at all. Reading the competition table runs those checks inside this
            # same borrow, so game_db is still decompressed once. Without a map every
            # competition_name is None anyway, so nothing is read on its account.
            if context.competition_names:
                self.competitions()
            stage_index = context.stage_index()
            competition_index = context.competition_index()
            # The stadium table is read inside this same borrow, and its own checks run here,
            # so no ground uid reaches a fixture row from a table whose shape did not pass.
            stadium_index = self._checked_stadium_index()
            summaries = locate_match_summary_scores(
                game_db,
                find_match_summary_layout(
                    save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
                ),
            )
        del game_db
        span_records = context.span_records()
        fixtures, fixture_stats, fixture_offsets = build_fixtures_with_offsets(
            span_records, stage_index, competition_index, club_index, stadium_index, layout
        )
        fixtures, result_stats = self._scored_fixtures(
            fixtures,
            span_records,
            stage_index,
            find_result_layout(save_info.build),
            summaries=summaries,
            fixture_offsets=fixture_offsets,
        )
        fixture_check = _checks.check_fixtures(
            fixture_stats, result_stats, gate_bounds, span_records.span_bytes
        )
        self._enforce_checks((fixture_check,))
        self._store_reader_checks((fixture_check,))
        return Table(fixtures, Fixture)

    def _scored_fixtures(
        self,
        fixtures: tuple[Fixture, ...],
        span_records: SpanRecords,
        stage_index: StageIndex,
        layout: StageResultLayout,
        *,
        summaries: MatchSummaryScores | None = None,
        fixture_offsets: tuple[int, ...] = (),
    ) -> tuple[tuple[Fixture, ...], ResultStats]:
        """Join stage results, owned summaries and physically bound calendar packet scores.

        The records come from the span pass, which collected them on what each one settles by
        itself, and from the sections the layout names, read one at a time. Both routes are
        then judged by the one `result_in_scope` predicate, so neither can accept what the
        other would not.

        The window a record is accepted in is the calendar's own first and last date, taken
        from the calendar this very call built. A calendar holding no dated match at all
        therefore accepts nothing, rather than falling back on some wider rule: with no fixture
        to join, no score could be attributed anyway.

        A section the save does not list is skipped rather than raising, since a save need not
        carry every one of them.

        Summaries use a separate exact date/competition/team key and cannot replace a known
        score or revive a contradiction between stage results. Their counts remain separate
        from the stage locator's checks.
        Calendar packets use the builder's sorted physical offsets, preserve existing and
        partial scores, and cannot revive a stage or summary contradiction.
        """
        context = self._context
        # The stage table is a rejection filter here and nothing else: this join asks only
        # whether a record's stage id is one the table holds, and copies no value out of it, so
        # no score it produces carries anything of that index. That is why this reads the
        # cached index instead of going through `stages()`, which would enforce that reader's
        # _checks. Taking only a membership test is what fails safe: a stage table that had
        # moved would cost scores here and could never invent one, which is the opposite of the
        # defect the rule about handing another reader's data out unchecked exists to stop.
        # A fixture row does carry stage-derived fields, its competition and round among them,
        # but `build_fixtures` puts them there; they do not arrive through this join.
        stage_by_id = stage_index.stage_by_id
        if fixture_offsets and len(fixture_offsets) != len(fixtures):
            raise ValueError("fixture offsets do not match the sorted calendar")
        scores_by_offset: dict[int, tuple[int, int] | None] = {}
        for raw in span_records.fixture_scores:
            score = (
                None
                if raw.home_goals is None or raw.away_goals is None
                else (raw.home_goals, raw.away_goals)
            )
            if raw.span_offset in scores_by_offset and scores_by_offset[raw.span_offset] != score:
                scores_by_offset[raw.span_offset] = None
            else:
                scores_by_offset[raw.span_offset] = score
        packet_scores = {
            position: scores_by_offset[offset]
            for position, offset in enumerate(fixture_offsets)
            if offset in scores_by_offset
        }
        covered_dates = calendar_dates(fixtures)
        if covered_dates is None:
            return apply_results(
                fixtures,
                (),
                candidates=span_records.result_candidates,
                summaries=summaries,
                packet_scores=packet_scores,
            )
        earliest_date, latest_date = covered_dates
        candidates = span_records.result_candidates
        collected = [
            raw_result
            for raw_result in span_records.results
            if result_in_scope(raw_result, stage_by_id, earliest_date, latest_date)
        ]
        listed_sections = self._require_open().sections
        for section_name in layout.regions:
            if section_name not in listed_sections:
                continue
            with context.section(section_name) as section_bytes:
                located = locate_stage_results(
                    section_bytes, layout, stage_by_id, earliest_date, latest_date
                )
            candidates += located.candidates
            collected.extend(located.results)
        return apply_results(
            fixtures,
            collected,
            candidates=candidates,
            summaries=summaries,
            packet_scores=packet_scores,
        )

    def stadiums(self) -> Table[Stadium]:
        """Every ground the save's database holds, in the order the save stores them.

        A row carries the ground's capacities, its pitch, when it was built and rebuilt, and
        the club that **owns** it. Most rows carry no name: the game takes a ground's name from
        its installed database and only a couple of hundred grounds store one in the save.

        `home_club_uids` says which clubs play their home matches there, and it is **not a
        stored link**: no club record points at a ground, so it comes from the fixture
        calendar, as the ground a club used for most of its first-team home matches. A ground
        no club used often enough lists none, and a shared ground lists every club that uses
        it. Owning a ground and playing at it are different things and are separate fields.

        **A ground with no stored owner is the council's.** The game's facilities screen shows
        one such ground as owned by the council, so an empty `owner_club_uid` is what the game
        displays that way rather than an owner fmsave failed to read.

        The table's closing header marks the end of its ground records and is not returned
        as a ground.

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No stadium table was found, or a stadium uid appears in two
                rows. The club and fixture readers run first and raise here too, since a row
                carries club names and a calendar-derived link.

        Warns:
            ReaderCheckWarning: On a full-size save, what the table or the calendar link
                decoded falls outside the checks' bounds. The club and fixture checks run here
                as well. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(STADIUMS_TABLE_CACHE_KEY, self._read_stadiums)

    def _read_stadiums(self) -> Table[Stadium]:
        context = self._context
        gate_bounds = self._gate_bounds()
        # The calendar and the clubs are read first and in full, checks and all: a stadium row
        # carries its owner's club name and a home-ground link built out of fixture rows, so
        # neither may reach it from a table whose own checks did not pass.
        fixtures = self.fixtures()
        self.clubs()
        # No game_db borrow here on purpose. The calendar above reads the club and stadium
        # indexes inside its own borrow, so both are cached by now and a borrow would only
        # decompress that section a second time for two lookups already in hand.
        club_index = context.club_index()
        stadium_index = self._checked_stadium_index()
        stadiums, stadium_stats = build_stadiums(
            stadium_index, club_index, tuple(fixtures), self._stadium_layout()
        )
        stadium_check = _checks.check_stadiums(
            stadium_stats, gate_bounds, stadium_index.game_db_bytes
        )
        self._enforce_checks((stadium_check,))
        self._store_reader_checks((stadium_check,))
        return Table(stadiums, Stadium)

    def _stadium_layout(self) -> StadiumTableLayout:
        save_info = self._context.info
        return find_stadium_layout(save_info.section_schemas.get(GAME_DB_SECTION), save_info.build)

    def _checked_stadium_index(self) -> StadiumIndex:
        """The shared stadium index, once the table's own checks have passed.

        Both readers that use the index take it through here, so no ground uid leaves fmsave
        from a table whose shape was never judged. Only the table's own checks run: the
        home-ground share needs the calendar, which is read after this index and judged by the
        stadium reader instead.
        """
        context = self._context
        stadium_index = context.stadium_index()
        table_stats = stadium_table_stats(
            stadium_index, context.club_index(), self._stadium_layout()
        )
        self._enforce(
            _checks.STADIUMS_READER,
            _checks.evaluate_stadium_table(
                table_stats, self._gate_bounds(), stadium_index.game_db_bytes
            ),
        )
        return stadium_index

    def transfer_windows(self) -> Table[TransferWindow]:
        """Every transfer window the save's rules database holds, in stored order.

        A window says when a transfer window opens and closes in a season. It is database
        content rather than career state: every save made from one installed database holds
        the same windows, whatever has happened in the career. The dates are season-relative,
        so each carries an offset from the season's start year rather than a calendar date,
        and a window has no name of its own. The table is read on the first call; later calls
        return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.

        Warns:
            ReaderCheckWarning: On a full-size save, fewer windows were decoded than the checks
                allow, or the windows that were found did not decode their dates. A save opened
                with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(TRANSFER_WINDOWS_TABLE_CACHE_KEY, self._read_transfer_windows)

    def injury_types(self) -> Table[InjuryType]:
        """Every injury the game can hand out that the save names, in stored order.

        The names are the game's own text, as the save stores it, in the language the save was
        written in. They are in no section of the save: each per-match file it holds carries
        one copy of the table, so **a save with no per-match file has no names at all** and
        this table is then empty. Some injury codes have no entry in the table, so a code an
        injury carries need not be named here. This table holds only what the save itself
        stores: fmsave ships no injury names of its own, so a code the save leaves out has no
        name here or anywhere else.

        Only as many per-match files are read as it takes to find the table, whatever a save
        lists, and no game database is read at all. The table is read on the first call; later
        calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: A per-match file is damaged or was being written.

        Warns:
            ReaderCheckWarning: On a full-size save listing at least one per-match file, fewer
                records of the table were read than the checks allow. A save opened with
                strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(INJURY_TYPES_TABLE_CACHE_KEY, self._read_injury_types)

    def _read_injury_types(self) -> Table[InjuryType]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        layout = find_injury_type_layout(save_info.build)
        # The full-size test runs on the size the directory declares for the game database, so
        # this reader decompresses nothing but the one per-match entry it reads.
        declared_game_db_bytes = next(
            (
                section.decompressed_size
                for section in save_info.sections
                if section.name == GAME_DB_SECTION
            ),
            0,
        )
        injury_types, injury_type_stats = read_injury_types(
            context.match_file_entries(), context.read_match_file, layout
        )
        injury_type_check = _checks.check_injury_types(
            injury_type_stats, gate_bounds, declared_game_db_bytes
        )
        self._enforce_checks((injury_type_check,))
        self._store_reader_checks((injury_type_check,))
        return Table(injury_types, InjuryType)

    def injuries(self) -> Table[InjuryRecord]:
        """Every injury the save still remembers, in stored order, of both kinds.

        A `HISTORY` row is an injury the save remembers happening: when it happened, the team
        the person was at, whether it happened in training or in a match, and how bad it was,
        both of those in the game's own words. **The save keeps only about the last two years
        of them**: the oldest row on every save measured is 742 days before the in-game date,
        and rows older than that are gone rather than kept, so this is a rolling window and not
        a whole career.

        **These are not the rows the game's Injury History tab lists.** That tab reads the
        full-career store, which fmsave does not ship because nothing in it says which person a
        history belongs to: it shows injuries from years outside this window, so what is here
        is the recent part of the career that tab shows whole.

        A `TYPED` row carries the injury type of a recent or current episode, and **its date is
        the day the player is expected back** rather than the day he was hurt, which is why so
        many of these dates sit ahead of the in-game date: adding each displayed injury's date
        to the time it kept the player out lands on the date stored here, checked on eleven
        players. A date behind the in-game date is a return the game has already reached, and
        how far behind those go depends on the save, so nothing here treats a week as a rule.
        A typed row is **not a list of injuries the player has recovered from**: what it names
        is the type, which no `HISTORY` row carries. About one type code in fifteen has no entry
        in `Save.injury_types`, and `type_name` is empty for those: fmsave ships no injury
        names of its own.

        A row whose person the save no longer keeps as a player leaves `player_uid` and
        `player_name` empty, which is about one `HISTORY` row in twenty. A `HISTORY` row whose
        team no club lists, or which names no team at all, leaves `team_id` and the three club
        fields empty rather than guessing; that is about one row in five hundred. Two views
        this table has no field for::

            history = career_save.injuries()
            own = history.where(player_uid=player_uid)
            typed_date = next(row.date for row in own if row.kind == "typed")
            # The latest history row on or before a typed row's date, for the same player.
            before = [
                row.date
                for row in own
                if row.kind == "history" and row.date is not None and row.date <= typed_date
            ]
            days_between = (typed_date - max(before)).days if before else None

        `days_between` is the gap between two dates and never how long the player was out for,
        which no row of this table holds. Filtering by a player's club today is
        `where(player_uid=...)` against `Save.players`, since `club_uid` here is the club at
        the time.

        This reader joins through the player records, so **a cold call pays the player pass**
        over the game database; a warm one decompresses only this section. The table is read on
        the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The save's in-game date is unreadable, so an injury date cannot
                be judged against it; a count in the section runs past the end of it, the
                section's tail is not where it belongs, or bytes follow it; or no club or
                player record is accepted.

        Warns:
            ReaderCheckWarning: On a full-size section, the rows fall outside the checks'
                bounds. Every index whose data this reader hands out is read through the reader
                that enforces that index's own checks, so those checks are reported here as
                well. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(INJURIES_TABLE_CACHE_KEY, self._read_injuries)

    def _read_injuries(self) -> Table[InjuryRecord]:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so an injury's "
                "date cannot be judged against it"
            )
        gate_bounds = self._gate_bounds()
        layout = find_injury_manager_layout(
            save_info.section_schemas.get(INJURY_MANAGER_SECTION), save_info.build
        )
        # The names this reader hands out come from three tables, so each is read through the
        # reader that enforces its own checks rather than through a raw index: a player name,
        # a club name and an injury-type name all leave fmsave here, and none of them may come
        # from a table whose shape was never judged.
        injury_types = self.injury_types()
        with context.section(INJURY_MANAGER_SECTION) as injury_manager:
            walk = walk_injury_manager(injury_manager, layout, save_info.file_name)
            # One game_db borrow covers both indexes the joins go through, so a cold call
            # decompresses that section once rather than once per index.
            with context.section(GAME_DB_SECTION):
                players = self.players()
                self.clubs()
                player_records = context.player_records()
                club_index = context.club_index()
            injuries, injury_stats = build_injury_records(
                injury_manager,
                walk,
                player_records,
                players,
                club_index,
                injury_types,
                clock,
                layout,
            )
        injury_check = _checks.check_injuries(injury_stats, gate_bounds)
        self._enforce_checks((injury_check,))
        self._store_reader_checks((injury_check,))
        return Table(injuries, InjuryRecord)

    def affiliates(self) -> Table[AffiliateGroup]:
        """Every group of clubs the save stores together, in stored order.

        **What groups a set of clubs is not established.** These groups live in a section of
        their own and carry nothing that says what the grouping means, so every club field is
        `unconfirmed`.

        **They are not the affiliates a club's Affiliated Clubs screen lists.** The club whose
        screen listed 26 affiliates belongs to no group here, and the one group naming a club
        that screen also names pairs it with its own academy rather than with the viewing club.
        A multi-club ownership group is recognisable in the largest group of every save
        measured, which would suit an ownership reading, but no screen has said so. So a club's
        own affiliates, and the kind of each affiliation, are in no field fmsave reads.

        This is **not** the parent link `Club.parent_club_uid` carries, which comes from the
        team lists inside the club records; the two relations share no pair at all, although
        the parent link is what a club's B and C sides on that screen come through. A member
        whose stored club index no club record claims leaves that entry's uid and name empty
        rather than being guessed, which is about one member in sixty.

        The other members of the groups a club belongs to, without the club itself::

            groups = career_save.affiliates()
            own_groups = groups.filter(lambda group: club_uid in group.club_uids)
            others = tuple(
                member_uid
                for group in own_groups
                for member_uid in group.club_uids
                if member_uid is not None and member_uid != club_uid
            )

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The group section is too short to hold its header, a group's
                member count is outside what a group may hold, a group runs past the end of
                the section, the groups do not end on the section's last byte, no club record
                is accepted, a club uid or club index appears in two records, or a team id is
                listed twice.

        Warns:
            ReaderCheckWarning: On a full-size save whose groups hold a member, fewer members
                resolve to a club than the checks allow, or the club table falls outside its
                own bounds. A save opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(AFFILIATES_TABLE_CACHE_KEY, self._read_affiliates)

    def _read_affiliates(self) -> Table[AffiliateGroup]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        layout = find_affiliate_layout(
            save_info.section_schemas.get(FEEDER_SECTION), save_info.build
        )
        with context.section(FEEDER_SECTION) as feeder:
            stored_groups = walk_affiliate_groups(feeder, layout, save_info.file_name)
        # The club index hands its names and uids straight out on every row, so it is read
        # through the reader that enforces the club checks rather than through the raw index.
        # It is the one index this reader needs, and it carries the section length the checks
        # want, so nothing here borrows game_db: the index's own borrow is the only one, and a
        # warm call decompresses nothing at all.
        self.clubs()
        club_index = context.club_index()
        groups, affiliate_stats = build_affiliate_groups(stored_groups, club_index)
        affiliate_check = _checks.check_affiliates(
            affiliate_stats, gate_bounds, club_index.game_db_bytes
        )
        self._enforce_checks((affiliate_check,))
        self._store_reader_checks((affiliate_check,))
        return Table(groups, AffiliateGroup)

    def job_vacancies(self) -> Table[JobVacancy]:
        """Every open job the save's job-centre feed holds, in stored order.

        **The feed keeps old rows.** The earliest advertised date on the saves measured is
        about ten years before the in-game date, and nothing in a row says whether the job has
        since been filled, so this is what the save still remembers rather than what the game
        would list today.

        A vacancy is stored against a team, so `team_id` is the save's own key and the club
        fields come from the club that fields that team; a team no club lists leaves them
        empty, and a record naming no team at all leaves `team_id` empty too.
        `league_position` is the team's current position in the competition the row
        names, which is empty on about a quarter of rows because the save stores none. The job
        title, the second date and two further numbers have no confirmed meaning and ship in
        `unknown` rather than under names they have not earned.

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The feed section is too short to hold its header, or its size is
                not its header and its record size times the count it claims; the save's
                in-game date is unreadable, so an advertised date cannot be judged against it;
                no club record is accepted; a club uid or club index appears in two records; a
                team id is listed twice; or no stage table was found in the tail of the game
                database. With a competition name map the competition reader runs first and
                raises here too, so no row is named from a table that could not be read.

        Warns:
            ReaderCheckWarning: On a feed of at least twenty records, the records fall outside
                the checks' bounds. The club and stage tables' checks run here as well, and
                with a name map the competition table's. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(JOB_VACANCIES_TABLE_CACHE_KEY, self._read_job_vacancies)

    def _read_job_vacancies(self) -> Table[JobVacancy]:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so a vacancy's "
                "advertised date cannot be judged against it"
            )
        gate_bounds = self._gate_bounds()
        layout = find_job_centre_layout(
            save_info.section_schemas.get(JOB_CENTRE_SECTION), save_info.build
        )
        # One game_db borrow covers both indexes the joins go through, so a cold call
        # decompresses that section once rather than once per index. The feed section is a few
        # kilobytes, so holding it across that borrow costs nothing.
        with context.section(JOB_CENTRE_SECTION) as job_centre:
            with context.section(GAME_DB_SECTION):
                # The club index hands out a club name and a team slot on every row, so it is
                # read through the reader that enforces its own _checks. With a name map the
                # competitions are read the same way and for the same reason, since every
                # competition name a row carries comes out of that index; without one every
                # competition_name is None anyway, so the id-pair pass is never paid for.
                self.clubs()
                if context.competition_names:
                    self.competitions()
                club_index = context.club_index()
                competition_index = context.competition_index()
            vacancies, vacancy_stats = read_job_vacancies(
                job_centre,
                club_index,
                competition_index,
                clock,
                layout,
                save_info.file_name,
            )
        vacancy_check = _checks.check_job_vacancies(vacancy_stats, gate_bounds)
        self._enforce_checks((vacancy_check,))
        self._store_reader_checks((vacancy_check,))
        return Table(vacancies, JobVacancy)

    def league_tables(self) -> Table[LeagueTable]:
        """Every live league table the save holds, in the order the save stores them.

        One table is one run of blocks the save stores together, told from the next by the
        index each block keeps of its own place in its table. The save stores each block
        several times over, the copies agreeing in every field fmsave decodes and differing
        only in undecoded head bytes, so repeated content is dropped before the tables are
        built; keeping it would break the tables apart. Nothing in a table names its
        competition, so it is voted for from the fixture calendar and is empty on the few
        tables the vote cannot settle, which are still returned; one competition names
        several tables, since a cup's group stage holds a table per group. Rows are in the
        order the save stores, which is the table's own standings order, so `position` is the
        league position. Each match slot says whether it was played at home or away, from the
        parity the save alternates venue by; the same calendar checks that parity on every
        table whose results account for one season of it. The table is read on the first call;
        later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted; a club uid or club index appears in
                two records; a team id is listed twice; no stage table was found in the tail of
                the game database; a stage id appears in two rows; or the save's in-game date
                is unreadable.

        Warns:
            ReaderCheckWarning: On a full-size span, the blocks fall outside the checks'
                bounds. Every index whose data this reader hands out is read through the
                accessor that enforces that index's own checks, so the checks of the fixture
                calendar the vote runs on, and of the club, stage and competition tables this
                reader joins through, are reported here as well. A save opened with strict=True
                raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(LEAGUE_TABLES_TABLE_CACHE_KEY, self._read_league_tables)

    def _read_league_tables(self) -> Table[LeagueTable]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        layout = find_layout(LeagueTableLayout, SPAN_REGION, None, save_info.build).layout
        # The vote runs on the calendar this reader asks the fixtures reader for, not on the
        # span's raw fixture records, so every row it counts comes from a table whose own
        # checks have passed: a calendar that had shattered into fragments, or swallowed the
        # block of template matches no save plays, would otherwise vote a competition onto
        # hundreds of tables and raise nothing at all.
        fixtures_table = self.fixtures()
        # Every index this reader borrows is taken through the accessor that enforces that
        # index's own checks, never through the raw context index, because this reader hands
        # the borrowed data straight out: club names and team slots on every row, competition
        # ids on every table, and the stage joins the calendar vote runs on. Forcing the club,
        # competition or stage bounds to something unmeetable must be reported on this call, not
        # leave it returning thousands of club names from an index whose checks never ran. On a
        # strict save that stops the call; on any other it warns here too. The calendar
        # above already built and cached all three indexes inside one game_db borrow, so these
        # are cache reads plus their checks, and this reader decompresses nothing of its own.
        self.clubs()
        self.stages()
        self.competitions()
        club_index = context.club_index()
        competition_index = context.competition_index()
        span_records = context.span_records()
        league_tables, table_stats = build_league_tables(
            span_records, fixtures_table, competition_index, club_index, layout
        )
        table_check = _checks.check_league_tables(table_stats, gate_bounds, span_records.span_bytes)
        self._enforce_checks((table_check,))
        self._store_reader_checks((table_check,))
        return Table(league_tables, LeagueTable)

    def competition_rules(self) -> Table[CompetitionRules]:
        """Every competition-rules block the save holds, in the order the save stores them.

        A block carries a competition's promotion, play-off and relegation places, its
        tie-break codes, its prize money by finishing position and its round calendar.

        **A row's competition comes from where the save keeps the block, not from a field it
        stores.** The span alternates rules blocks and league-table blocks, and the table
        stored right after a block is the one that block's rules govern. `competition_id` and
        `competition_name` are that table's, and are empty where the run of blocks after the
        preamble is not exactly one table `league_tables()` returned with a competition of its
        own, which on the saves measured is 32% to 45% of rows. It is a position in the file
        rather than a stored link, and the competition it hands over is itself a vote on the
        fixture calendar, so both fields are as strong as `LeagueTable.competition_id` and no
        stronger. A block's club count and its points deduction for administration are not read
        at all, because no fixed position in the block carries either; the linked table's own
        `club_count` is where a club count comes from.

        The squad and financial rules the save's rules database holds are not read: nothing
        readable ties one of those groups to a competition, and their content is database
        content, identical on every save of one installed database. So `kind` is PREAMBLE on
        every row. Transfer windows are their own table, `transfer_windows()`.

        **A cold call builds the league tables and the fixture calendar**, since that is where
        the competition comes from. A caller who has already read either pays nothing extra;
        one who has read neither pays for both here. The table is read on the first call; later
        calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted; a club uid or club index appears in
                two records; a team id is listed twice; no stage table was found in the tail of
                the game database; a stage id appears in two rows; no stadium table was found;
                or the save's in-game date is unreadable, so the span pass cannot run.

        Warns:
            ReaderCheckWarning: On a full-size span, the blocks or the link fall outside the
                checks' bounds. The checks of the league tables this reader links to, of the
                fixture calendar their vote runs on, and of the club, stage and competition
                tables those readers join through, are reported here as well. A save opened
                with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(COMPETITION_RULES_TABLE_CACHE_KEY, self._read_competition_rules)

    def _read_competition_rules(self) -> Table[CompetitionRules]:
        context = self._context
        gate_bounds = self._gate_bounds()
        # The link reads the tables this reader asks the league-table reader for, not the
        # span's raw table blocks, so every set of clubs it matches comes from a table whose
        # own checks have passed: a table decode that had shattered, or run two tables
        # together, would otherwise hand over sets that match nothing and leave every row
        # unlinked without raising at all. That call builds the calendar too, which is where
        # the round dates the link is checked by come from, and it takes the club, stage and
        # competition indexes through their own checked readers.
        league_tables = self.league_tables()
        fixtures_table = self.fixtures()
        competition_index = context.competition_index()
        span_records = context.span_records()
        rules, rules_stats = build_competition_rules(
            span_records, league_tables, fixtures_table, competition_index
        )
        rules_check = _checks.check_competition_rules(
            rules_stats, gate_bounds, span_records.span_bytes
        )
        self._enforce_checks((rules_check,))
        self._store_reader_checks((rules_check,))
        return Table(rules, CompetitionRules)

    def player_match_stats(self) -> Table[PlayerMatchStats]:
        """Every match one of the save's players played that it still holds a record of.

        Rows come in player order and, inside each player, in the order the save stores his
        matches. **This is never a whole season and never a career**: the save keeps about
        twenty matches per player per spell at a team, **counted across all competitions at once
        rather than per competition**, and drops the oldest as new ones arrive. A player who has
        played more than that in his current spell has only his latest matches here, so **a
        per-competition total summed from these rows is short without saying so**. Nothing in a
        row marks it as truncated. Friendlies, internationals and youth matches are kept apart
        from these records and are not here at all.

        Each row carries the competition id the record itself stores, which is in the stage id
        space, and joins to a club through the opponent's team id; a team id no club lists
        leaves the opponent fields empty rather than guessing them. A match the save no longer
        holds the statistics of carries its date, competition and opponent, `has_stats` is
        false, and every field the statistics would fill is empty.

        On a full-size save, an empty table passes this reader's checks only when every
        accepted player has an independently located null or explicitly empty stored history.
        An unsupported or malformed predecessor remains unresolved; it is not treated as an
        empty history.

        This reader decodes the players to fill `player_name`, so a cold call pays for the
        player pass; a caller who has already called `players()` pays nothing extra for it. The
        table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted; a club uid or club index appears in
                two records; a team id is listed twice; no player records were found; two
                player records share a uid; no stage table was found in the tail of the game
                database; or the save's in-game date is unreadable, so the years a match may be
                dated in cannot be worked out.

        Warns:
            ReaderCheckWarning: On a full-size save, the records decoded fall outside the
                checks' bounds. The checks of the club and player readers this one joins
                through are reported here as well. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(PLAYER_MATCH_STATS_TABLE_CACHE_KEY, self._read_player_match_stats)

    def _read_player_match_stats(self) -> Table[PlayerMatchStats]:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so the years a "
                "match record may be dated in cannot be worked out"
            )
        gate_bounds = self._gate_bounds()
        layout = find_match_record_layout(
            save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
        )
        # One game_db borrow covers the record search and every index the joins go through, so a
        # cold call decompresses that section once rather than once per index.
        with context.section(GAME_DB_SECTION) as game_db:
            # These two hand their data straight out: the player uid and name on every row, and
            # the opponent club's names and team slot. Each is therefore read through the reader
            # that enforces its own checks, never through the raw index behind it, so forcing
            # the player or club bounds to something unmeetable stops this call instead of
            # leaving it handing out names from an index whose checks never ran. Both run inside
            # this borrow, so they still share the one decompression.
            players = self.players()
            self.clubs()
            club_index = context.club_index()
            player_records = context.player_records()
            # The stage index is read straight from the cache, without the stage reader's
            # checks, because nothing of it reaches a caller: a record carries its own
            # competition id, and this index is used only to count how many of those ids the
            # stage table names, which is what one of this reader's own checks judges.
            stage_index = context.stage_index()
            records_by_position = locate_match_records(game_db, player_records, layout, clock)
            game_db_length = len(game_db)
        match_rows, match_stats = build_player_match_stats(
            records_by_position, player_records, players, club_index, stage_index, layout
        )
        match_check = _checks.check_player_match_stats(match_stats, gate_bounds, game_db_length)
        self._enforce_checks((match_check,))
        self._store_reader_checks((match_check,))
        return Table(match_rows, PlayerMatchStats)

    def player_season_stats(self) -> Table[PlayerSeasonStats]:
        """Every player's stats for the current season, as the squad and player screens show them.

        One row per competition type (`SeasonStatsKind`) and team. `OVERALL` is the season
        total. A player also has rows for any other team they played for this season, such as a
        B team or a club they left. Rows carry the game's per-90 and percentage figures too; see
        `PlayerSeasonStats`.

        This reader decodes the players to fill `player_name`, so a first call also pays for
        `players()`. The table is read on the first call; later calls return the same table. A
        full save gives about 400,000 rows, which takes a few seconds and a few hundred
        megabytes.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The season statistics are missing or not laid out as expected,
                or the club or player reader this one joins through fails.

        Warns:
            ReaderCheckWarning: On a full-size save, the records decoded fall outside the
                checks' bounds. The checks of the club and player readers this one joins
                through are reported here as well. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(PLAYER_SEASON_STATS_TABLE_CACHE_KEY, self._read_player_season_stats)

    def _read_player_season_stats(self) -> Table[PlayerSeasonStats]:
        context = self._context
        gate_bounds = self._gate_bounds()
        layout = find_season_stats_layout(context.info.build)
        body, walk = read_season_stats_section(self._container_index, layout)
        # One game_db borrow covers the player and club readers, so a cold call decompresses
        # that section once. Both are read through the readers that enforce their own checks,
        # since their names and teams reach every row.
        with context.section(GAME_DB_SECTION) as game_db:
            players = self.players()
            self.clubs()
            club_index = context.club_index()
            player_records = context.player_records()
            game_db_length = len(game_db)
        pindexes = player_records.pindexes
        position_by_uid = player_records.position_by_uid
        players_by_pindex = {
            pindexes[position_by_uid[player.uid]]: SeasonPlayer(
                uid=player.uid,
                name=player.name,
                team_id=player.team_id,
                goalkeeper=GOALKEEPER_POSITION in player.natural_positions,
            )
            for player in players
        }
        rows, stats = build_season_stats(
            walk, body, players_by_pindex, club_index.team_to_club, club_index.club_by_uid, layout
        )
        season_check = _checks.check_season_stats(stats, gate_bounds, game_db_length)
        self._enforce_checks((season_check,))
        self._store_reader_checks((season_check,))
        return Table(rows, PlayerSeasonStats)

    def player_season_history(self) -> Table[PlayerSeasonHistory]:
        """Archived player statistics, including completed seasons retained by the save.

        Rows carry the same statistics and computed rates as `PlayerSeasonStats`, together
        with an unconfirmed candidate season year and competition reference. Stored order
        need not be chronological. Detailed counts may be sparse for imported history;
        zeros are returned as stored. Goalkeeper fields use current natural positions.
        A club or nation export scope selects players by their current membership.

        The first call also reads players and clubs. Later calls return the cached table.
        Missing archive/index structures and malformed or ambiguous ownership raise
        `ReaderCheckError`. A valid empty history returns an empty table. Reader checks of
        players and clubs apply as usual. Closing the save releases its cached tables.
        """
        return self._context.cached(
            PLAYER_SEASON_HISTORY_TABLE_CACHE_KEY, self._read_player_season_history
        )

    def _read_player_season_history(self) -> Table[PlayerSeasonHistory]:
        context = self._context
        layout = find_history_layout(context.info.build)
        if ARCHIVE_SECTION not in self._container_index.sections:
            raise ReaderCheckError(
                f"{context.info.file_name}: historical season statistics archive is missing"
            )
        index = read_history_index(self._container_index, layout)
        with context.section(GAME_DB_SECTION):
            players = self.players()
            self.clubs()
            club_index = context.club_index()
        selectors = cast(Mapping[int, int], context.cached_value(HISTORY_SELECTORS_CACHE_KEY))
        history_players = {
            player.uid: SeasonPlayer(
                player.uid,
                player.name,
                player.team_id,
                GOALKEEPER_POSITION in player.natural_positions,
            )
            for player in players
        }
        with context.section(ARCHIVE_SECTION) as archive:
            rows, stats = build_history(
                index,
                archive,
                selectors,
                history_players,
                club_index.team_to_club,
                club_index.club_by_uid,
                find_season_stats_layout(context.info.build),
                context.info.file_name,
                layout,
            )
        history_check = _checks.check_season_history(stats)
        self._enforce_checks((history_check,))
        self._store_reader_checks((history_check,))
        return Table(rows, PlayerSeasonHistory)

    def finances(self) -> Table[FinanceMonth]:
        """Every month of club money the save keeps, by club and then oldest month first.

        **Only some clubs have a series at all.** The save keeps one for the clubs of the one or
        two league nations it tracks, not for every club it holds, and which nations those are
        changes as a career moves on, so a club with no rows here is ordinary rather than a
        failure. On the saves measured 57 to 335 clubs of the 48,000 to 51,000 each save holds
        had one, of between 3 and 60 months each; 60 months is as many as a club keeps. A save
        whose clubs keep none at all returns an empty table, and on a save with no human manager
        that is also what a search finding nothing would return: the checks bound the rows that
        were decoded, and the one count they bound from below applies only where the save lists
        a managed club. `fmsave validate` reports the clubs with a series and the club records
        searched either way.

        `balance` is the balance at the **end** of the row's month, and `net_transfers` is
        positive for a net **spend**. **Money is a whole number in the save's base currency,
        which is not the currency the game displays**: on the save whose screens were read the
        balance, both budgets, the wage bill and the month's income and expenditure all display
        at about 1.157 times the stored value, one rate fitting every one of them, which is
        what says the stored unit is its own unit. Nothing here is converted and no rate is
        applied. The weekly fields are weekly; every other money field is one month's amount.
        `transfer_budget_allocated` is **not** the budget the board allocated: that screen
        showed a budget well above it with almost none of it spent, so what the field is stays
        unnamed.

        `month` is worked out from the save's own date rather than stored: the last row of a
        club is the month before the save's month, which is the lag that put that club's two
        oldest rows on the months its own screen labelled them with. Several useful figures are
        arithmetic on these rows rather than fields: wage headroom is `wage_budget_weekly` less
        `wage_payroll_weekly`, a yearly figure is a weekly one times 52, a club's latest month
        is its last row, and a club summary is its rows grouped by `club_uid`.

        The table is read on the first call to `finances()` or `sponsorships()`, from one decode
        pass; later calls to either return the same tables. When a check of that pass fails,
        neither table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears in
                two records, a team id is listed twice, or the save's in-game date is
                unreadable, so no month can be dated.

        Warns:
            ReaderCheckWarning: On a full-size save, the months and sponsors decoded fall
                outside the checks' bounds, or the club table falls outside its own. A save
                opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(FINANCES_TABLE_CACHE_KEY, self._finances_table_entry_point)

    def sponsorships(self) -> Table[Sponsorship]:
        """Every sponsorship contract the save lists for a club, in stored order.

        The clubs are the ones `finances()` keeps a series for, in the same order, and each
        club's contracts keep the order the save stores them in. **The list keeps contracts that
        have ended**, and an ended contract's `annual_value` is often non-zero, so a club's
        current sponsorship income is the sum of `annual_value` over the rows whose `end` is
        after the save's date, not over every row.

        Every `type` code is UNKNOWN: the save groups its sponsorships into about twenty kinds
        and no displayed label has pinned one of those codes. Money is a whole number in the
        save's base currency, as in `finances()`.

        The table is read on the first call to `finances()` or `sponsorships()`, from one decode
        pass; later calls to either return the same tables. When a check of that pass fails,
        neither table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears in
                two records, a team id is listed twice, or the save's in-game date is
                unreadable, so no month can be dated.

        Warns:
            ReaderCheckWarning: On a full-size save, the months and sponsors decoded fall
                outside the checks' bounds, or the club table falls outside its own. A save
                opened with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(SPONSORSHIPS_TABLE_CACHE_KEY, self._sponsorships_table_entry_point)

    def _finances_table_entry_point(self) -> Table[FinanceMonth]:
        tables = self._decode_finance_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(SPONSORSHIPS_TABLE_CACHE_KEY, lambda: tables.sponsorships)
        return tables.finances

    def _sponsorships_table_entry_point(self) -> Table[Sponsorship]:
        tables = self._decode_finance_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(FINANCES_TABLE_CACHE_KEY, lambda: tables.finances)
        return tables.sponsorships

    def _decode_finance_tables(self) -> _FinanceTables:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so the month "
                "each finance row covers cannot be worked out"
            )
        gate_bounds = self._gate_bounds()
        layouts = find_finance_layouts(
            save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
        )
        # One game_db borrow covers the club records, the club index and the managed club, so a
        # cold call decompresses that section once rather than once per reader.
        with context.section(GAME_DB_SECTION) as game_db:
            # Every row carries a club name, so the club table is read through the reader that
            # enforces the club checks rather than through the index behind them: forcing
            # those bounds to something unmeetable must be reported on this call instead of
            # leaving it handing out names from an index whose checks never ran.
            self.clubs()
            # Whether a managed club exists is what decides whether the series floor applies,
            # and this reader hands out nothing of that table, but it is read through the same
            # accessor for the borrow it shares.
            managed_clubs = self.managed_clubs()
            club_index = context.club_index()
            months, sponsorships, finance_stats = read_club_finances(
                game_db,
                club_index,
                context.own_club_record_spans(),
                clock,
                layouts,
                len(managed_clubs) > 0,
            )
            game_db_length = len(game_db)
        # Both checks run before either table is built: when one fails, nothing is cached and
        # the next call decodes and checks again.
        reader_checks = (
            _checks.check_finances(finance_stats, gate_bounds, game_db_length),
            _checks.check_sponsorships(finance_stats, gate_bounds, game_db_length),
        )
        self._enforce_checks(reader_checks)
        return _FinanceTables(
            Table(months, FinanceMonth), Table(sponsorships, Sponsorship), reader_checks
        )

    def facilities(self) -> Table[ClubFacilities]:
        """Every club's corporate facilities rating, in club index order.

        **The clubs are the ones `finances()` covers**, because the rating is stored behind a
        club's monthly finance chain and only the clubs of the one or two league nations a save
        tracks keep one. A club with no rows in `finances()` has no row here either, which is
        most clubs of a save and is ordinary rather than a failure; a save whose clubs keep no
        series returns an empty table, and `fmsave validate` reports the counts.

        `corporate_facilities` is the rating the game's Facilities screen shows as a word on
        its **Corporate** line, and the words rise with the stored number. Fifteen of the
        twenty codes carry the word one club's own screen displayed against that exact number,
        from 1 Basic to 20 Excellent; two more, 8 and 14, carry the word of the codes either
        side of them, each of which a screen displayed the same word for. The three codes no
        club in the save carries -- 3, 4 and 16 -- read UNKNOWN with the raw number kept,
        rather than taking a word from where they sit on the scale. The screen's other facility
        lines, the stadium and pitch, the training and youth grounds and the academy, are not
        stored anywhere near this byte and are not read at all.

        The table is read on the first call; later calls return the same table.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: No club record is accepted, a club uid or club index appears in
                two records, or a team id is listed twice.

        Warns:
            ReaderCheckWarning: On a full-size save, the ratings decoded fall outside the
                checks' bounds, or the club table falls outside its own. A save opened with
                strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(FACILITIES_TABLE_CACHE_KEY, self._read_facilities)

    def _read_facilities(self) -> Table[ClubFacilities]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        game_db_schema = save_info.section_schemas.get(GAME_DB_SECTION)
        finance_layouts = find_finance_layouts(game_db_schema, save_info.build)
        layout = find_facility_layout(game_db_schema, save_info.build)
        # One game_db borrow covers the club records, the club index and the managed club, so a
        # cold call decompresses that section once rather than once per lookup.
        with context.section(GAME_DB_SECTION) as game_db:
            # Every row carries a club name, so the club table is read through the reader that
            # enforces the club checks rather than through the index behind them.
            self.clubs()
            # Whether a managed club exists is what decides whether the count floor applies.
            managed_clubs = self.managed_clubs()
            club_index = context.club_index()
            facilities, facility_stats = read_club_facilities(
                game_db,
                club_index,
                context.own_club_record_spans(),
                finance_layouts,
                layout,
                len(managed_clubs) > 0,
            )
            game_db_length = len(game_db)
        facility_check = _checks.check_facilities(facility_stats, gate_bounds, game_db_length)
        self._enforce_checks((facility_check,))
        self._store_reader_checks((facility_check,))
        return Table(facilities, ClubFacilities)

    def staff(self) -> Table[Staff]:
        """Everyone a club employs who is not a player, in the order their objects are stored.

        A row is one person at one club: the department lists the club keeps him in, what his
        contract pays and until when, his ability and the preferences a staff profile shows.
        **A person an affiliate side lists whose contract is with that side's parent is one row
        at the parent**, with the side that lists him in `listed_club_uid`, the same rule a
        player on a B team follows. A person a club lists but pays nothing has no contract to
        read, so his `wage` and both dates are empty rather than zero; about one listed person
        in seven of a save is like that.

        **The save's human manager is a row of his own**, with `is_human_manager` true. His
        object is laid out differently, so no ability, no preferences and none of the
        ability-block `unknown` keys read for him, while his name, birth date, personality and
        contract read as anyone's do.

        **The contract codes are not player squad statuses.** `unknown["contract_e36"]` comes
        from the byte a player's squad status is read from, but it takes different values on
        staff and no displayed label has named one, so it and the three codes beside it ship as
        raw numbers.

        **The job title is not readable, and `unknown["r4"]` is not it.** A club's staff screen
        settled that: over 78 displayed rows, 8 of the 16 codes on show carried two or more
        different job titles and 7 titles appeared under two or three different codes, so the
        byte keeps its raw number rather than becoming a named role. **The club's board is not
        in this table either**: the president, the director and the managing director appear on
        that same screen with no row here, while every other person on it matched a row.

        Several useful figures are arithmetic on these rows rather than fields: a club's
        non-playing wage bill is the sum of `wage` over its rows, how many of its staff it
        lists is `where(in_club_lists=True)`, and who it pays without listing is
        `where(has_contract=True, in_club_lists=False)`.

        The table is read on the first call to `staff()` or `staff_lists()`, from one decode
        pass; later calls to either return the same tables. When a check of that pass fails,
        neither table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written, a contract record runs
                past the end of the game database, or a name block's relation list runs past
                the window it was found in.
            ReaderCheckError: The club or player readers raised, or the save's in-game date is
                unreadable, so no contract can be dated.

        Warns:
            ReaderCheckWarning: On a full-size save, the staff decoded fall outside the checks'
                bounds, or the club or player checks this reader runs first do. A save opened
                with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(STAFF_TABLE_CACHE_KEY, self._staff_table_entry_point)

    def staff_lists(self) -> Table[StaffList]:
        """The three staff lists each club record holds, in club index order.

        A club that lists nobody has no row at all, and a club that lists somebody has all
        three rows, empty lists included. Only 733 to 1,957 of a save's 48,000 to 51,000 clubs
        list anybody, so most clubs are absent, which is ordinary rather than a failure.

        The lists split a club's staff into groups whose codes differ from list to list.
        **They look like the three departments a club's staff screen shows**: on one club the
        screen's medical, coaching and recruitment panels and that club's senior rows in lists
        0, 1 and 2 held the same people, person for person by name, save for the human manager
        and one contracted person no list holds. That is arithmetic on one club rather than a
        label on a list, so
        `list_index` stays a number. People a list names who turn out to be players are
        dropped, and `fmsave validate` reports how many; so are the few whose object cannot be
        told from another's, so a list's people are those `staff()` also has a row for. A
        list's size is `len(staff_uids)`.

        The table is read on the first call to `staff()` or `staff_lists()`, from one decode
        pass; later calls to either return the same tables. When a check of that pass fails,
        neither table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written, a contract record runs
                past the end of the game database, or a name block's relation list runs past
                the window it was found in.
            ReaderCheckError: The club or player readers raised, or the save's in-game date is
                unreadable, so no contract can be dated.

        Warns:
            ReaderCheckWarning: On a full-size save, the staff decoded fall outside the checks'
                bounds, or the club or player checks this reader runs first do. A save opened
                with strict=True raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(STAFF_LISTS_TABLE_CACHE_KEY, self._staff_lists_table_entry_point)

    def _staff_table_entry_point(self) -> Table[Staff]:
        tables = self._decode_staff_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(STAFF_LISTS_TABLE_CACHE_KEY, lambda: tables.staff_lists)
        return tables.staff

    def _staff_lists_table_entry_point(self) -> Table[StaffList]:
        tables = self._decode_staff_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(STAFF_TABLE_CACHE_KEY, lambda: tables.staff)
        return tables.staff_lists

    def _decode_staff_tables(self) -> _StaffTables:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so no staff "
                "contract can be dated"
            )
        gate_bounds = self._gate_bounds()
        layouts = find_staff_layouts(save_info.section_schemas, save_info.build)
        # One game_db borrow covers the club records, the player scan, the name pools and the
        # pass over the section, so a cold call decompresses that section once.
        with context.section(GAME_DB_SECTION) as game_db:
            # The player population decides which list values and which selectors belong to a
            # player, so a player pass whose own checks failed has to stop this reader too;
            # and every row carries a club name, so the clubs come through the reader that
            # enforces the club checks rather than through the index behind them.
            self.players()
            self.clubs()
            club_index = context.club_index()
            player_records = context.player_records()
            name_pools = context.name_pools()
            with context.section(HUMANS_SECTION) as humans:
                staff_rows, list_rows, staff_stats = read_staff(
                    game_db,
                    humans,
                    club_index,
                    player_records,
                    name_pools,
                    clock,
                    layouts,
                    save_info.file_name,
                )
            game_db_length = len(game_db)
        # Both checks run before either table is built: when one fails, nothing is cached and
        # the next call decodes and checks again.
        reader_checks = (
            _checks.check_staff(staff_stats, gate_bounds, game_db_length),
            _checks.check_staff_lists(staff_stats, gate_bounds, game_db_length),
        )
        self._enforce_checks(reader_checks)
        return _StaffTables(Table(staff_rows, Staff), Table(list_rows, StaffList), reader_checks)

    def tactics(self) -> Table[Tactic]:
        """Every tactic the manager's teams store, by team and then in stored order.

        **A tactic belongs to a team, not to a club.** The save keeps each team's own copy of
        every tactic the manager has, so the same tactic name appears once per team and a row
        is one stored copy, keyed on `team_id` and `index`. The copies are not byte-identical.
        **Nothing stored says which tactic is selected**, so there is no such field: the word
        that might hold it is the same on every block that carries a tactic at all.

        Only the manager's own teams are here. No other club stores a tactic in this form, and
        the line-ups the section keeps for thousands of other clubs are a different structure
        that fmsave does not read.

        `mentality` carries the word the game shows: the seven codes are the seven mentalities
        it offers, from Very Defensive to Very Attacking, confirmed against a manager's own
        tactics. **Every position bit is still a raw code with the label UNKNOWN**: the bits
        are read from offsets a strict walk of every record lands on exactly, but no displayed
        formation has been matched to one of those numbers. The 19 team instructions and the
        setting units of each slot are unidentified numbers in the same way, and ship in
        `unknown` and as `TacticSettingUnit` values rather than under names they have not
        earned.

        The table is read on the first call to `tactics()` or `set_pieces()`, from one walk;
        later calls to either return the same tables. When a check of that walk fails, neither
        table is kept, so both raise. A cold call pays for the player pass, because the
        selectors the reader's checks judge resolve through the player records.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The tactics section is too short to hold its header, a constant a
                team block is built around is not where fmsave expects it, a count inside a
                block runs past the end of the section, a name does not decode, no club record
                is accepted, a club uid or club index appears in two records, or a team id is
                listed twice.

        Warns:
            ReaderCheckWarning: On a full-size save that lists a managed club, what the walk
                read falls outside the checks' bounds. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(TACTICS_TABLE_CACHE_KEY, self._tactics_table_entry_point)

    def set_pieces(self) -> Table[SetPieceRoutine]:
        """Every set-piece routine slot of the manager's teams, by team and then slot.

        Every default routine and every member of a counted user-routine group is a row.
        `slot` gives stored order within the team, and `name` is None for an unnamed routine.
        Groups can contain multiple routines, so a team can have more than twenty rows.
        A routine is recognised by its record structure, never by its name.

        The table is read on the first call to `tactics()` or `set_pieces()`, from one walk;
        later calls to either return the same tables. When a check of that walk fails, neither
        table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The tactics section is too short to hold its header, a constant a
                team block is built around is not where fmsave expects it, a count inside a
                block runs past the end of the section, a name does not decode, no club record
                is accepted, a club uid or club index appears in two records, or a team id is
                listed twice.

        Warns:
            ReaderCheckWarning: On a full-size save that lists a managed club, what the walk
                read falls outside the checks' bounds. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(SET_PIECES_TABLE_CACHE_KEY, self._set_pieces_table_entry_point)

    def _tactics_table_entry_point(self) -> Table[Tactic]:
        tables = self._decode_tactics_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(SET_PIECES_TABLE_CACHE_KEY, lambda: tables.set_pieces)
        return tables.tactics

    def _set_pieces_table_entry_point(self) -> Table[SetPieceRoutine]:
        tables = self._decode_tactics_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(TACTICS_TABLE_CACHE_KEY, lambda: tables.tactics)
        return tables.set_pieces

    def _decode_tactics_tables(self) -> _TacticTables:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        layout = find_tactics_layout(
            save_info.section_schemas.get(TACTICS_SECTION), save_info.build
        )
        humans_layout = find_managed_club_layouts(save_info.section_schemas, save_info.build).humans
        # Every read of `game_db` sits inside one borrow, the managed club's own included, so a
        # cold call decompresses that section once. The managed-club reader needs it too, and
        # calling it before the borrow opened cost a second decompression of several hundred
        # megabytes. The two small sections are held across it, which costs a few megabytes.
        with (
            context.section(HUMANS_SECTION) as humans,
            context.section(TACTICS_SECTION) as tactics_section,
            context.section(GAME_DB_SECTION) as game_db,
        ):
            managed_clubs = self.managed_clubs()
            if not managed_clubs:
                return self._empty_tactic_tables(gate_bounds)
            managed_club_uid = managed_clubs[0].club_uid
            human_selector = first_human_selector(humans, humans_layout, save_info.file_name)
            header_selector, _header_blocks = read_tactics_header(
                tactics_section, layout, save_info.file_name
            )
            # Every row hands out a club name and the selector counts go through the players, so
            # both are read through the readers that enforce their own checks rather than
            # through the indexes behind them.
            self.clubs()
            players = self.players()
            club_index = context.club_index()
            player_records = context.player_records()
            game_db_length = len(game_db)
            managed_club = club_index.club_by_uid.get(managed_club_uid)
            club_team_ids = (
                [] if managed_club is None else [team.team_id for team in managed_club.teams]
            )
            blocks, walk_counts = walk_tactic_blocks(
                tactics_section, club_team_ids, layout, save_info.file_name
            )
        tactics, set_pieces, tactic_stats = build_tactic_tables(
            blocks,
            club_index,
            player_records,
            players,
            managed_club_uid,
            header_selector,
            human_selector,
            walk_counts,
        )
        # Both checks run before either table is built: when one fails, nothing is cached and
        # the next call walks and checks again.
        reader_checks = (
            _checks.check_tactics(tactic_stats, gate_bounds, game_db_length),
            _checks.check_set_pieces(tactic_stats, gate_bounds, game_db_length),
        )
        self._enforce_checks(reader_checks)
        return _TacticTables(
            Table(tactics, Tactic), Table(set_pieces, SetPieceRoutine), reader_checks
        )

    def _empty_tactic_tables(self, gate_bounds: GateBounds) -> _TacticTables:
        """Both tables empty, for a manager with no club: nothing here is judged."""
        empty_stats = _EMPTY_TACTIC_STATS
        reader_checks = (
            _checks.check_tactics(empty_stats, gate_bounds, 0),
            _checks.check_set_pieces(empty_stats, gate_bounds, 0),
        )
        return _TacticTables(Table((), Tactic), Table((), SetPieceRoutine), reader_checks)

    def training(self) -> Table[TeamTraining]:
        """The training calendar of each team of the club the save's manager runs.

        One row per team, in the order the save stores them: the first team, the reserves, the
        youth side and each team the club fields at a club it controls, which maps back to the
        managed club with the slot it holds in that club's list. **No other club has a
        calendar at all**, and a save whose manager runs no club returns an empty table.

        **Which week runs which schedule is settled.** Each weekly record holds the week's
        start date and then a schedule name, and the name is the schedule of the week whose
        date came before it: a manager's Training screen showed exactly that schedule for four
        consecutive weeks, where pairing each name with the following week would have been a
        week out on all four. The dates themselves are solid too: consecutive weeks step
        exactly seven days on every pair of every calendar measured, and the calendar runs from
        well before the save's date to well after it.

        The active week of a team is the latest one that has started. A week whose stored date
        does not decode carries None, and a save whose date is unreadable has nothing to
        compare against, so both are stepped around::

            clock = career_save.info.game_date
            weeks = career_save.training()[0].weeks
            started = [
                week
                for week in weeks
                if week.week_start is not None and clock is not None and week.week_start <= clock
            ]
            active = max(started, default=None, key=lambda week: week.week_start)

        What a schedule asks of a day is **not** read: each day of a week holds three codes
        whose meaning is unknown. `schedule_library` is the manager's own saved schedules,
        which the save keeps once per section rather than per team, so every row carries the
        same tuple, and the save may hold the same schedule twice over under two ids.

        The table is read on the first call to `training()` or `mentoring()`, from one walk;
        later calls to either return the same tables. When a check of that walk fails, neither
        table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The training section is too short to hold its header list, a
                block the walk accepted holds a weekly record or a mentoring group it cannot
                read, no club record is accepted, a club uid or club index appears in two
                records, a team id is listed twice, or no player record is found.

        Warns:
            ReaderCheckWarning: On a full-size save whose manager runs a club, the blocks and
                weeks read fall outside the checks' bounds. A save opened with strict=True
                raises ReaderCheckError instead.
        """
        context = self._context
        return context.cached(TRAINING_TABLE_CACHE_KEY, self._training_table_entry_point)

    def mentoring(self) -> Table[MentoringGroup]:
        """Every mentoring group of every team of the club the save's manager runs.

        A group belongs to a **team**, not to the club: the rows come team by team in the
        order the save stores the teams, and within a team in stored order. Only the managed
        club has groups at all, and a team with none has no row here, which is ordinary -- on
        the saves measured only the first team and one other side mentor anybody.

        `label` is the stored text. Every group of every save measured carries the game's own
        default wording with the group's number, and whether renaming a group in game changes
        what is stored has not been checked. A member whose stored selector names no player
        record leaves that entry's uid and name empty rather than guessing.

        The table is read on the first call to `training()` or `mentoring()`, from one walk;
        later calls to either return the same tables. When a check of that walk fails, neither
        table is kept, so both raise.

        Raises:
            SaveClosedError: The save is closed.
            SaveChangedError: The file changed on disk after it was opened.
            CorruptSaveError: The save is damaged or was being written.
            ReaderCheckError: The training section is too short to hold its header list, a
                block the walk accepted holds a weekly record or a mentoring group it cannot
                read, no club record is accepted, a club uid or club index appears in two
                records, a team id is listed twice, or no player record is found.

        Warns:
            ReaderCheckWarning: On a full-size save whose manager runs a club, the members read
                fall outside the checks' bounds. A save opened with strict=True raises
                ReaderCheckError instead.
        """
        context = self._context
        return context.cached(MENTORING_TABLE_CACHE_KEY, self._mentoring_table_entry_point)

    def _training_table_entry_point(self) -> Table[TeamTraining]:
        tables = self._decode_training_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(MENTORING_TABLE_CACHE_KEY, lambda: tables.mentoring)
        return tables.training

    def _mentoring_table_entry_point(self) -> Table[MentoringGroup]:
        tables = self._decode_training_tables()
        self._store_reader_checks(tables.reader_checks)
        self._context.cached(TRAINING_TABLE_CACHE_KEY, lambda: tables.training)
        return tables.mentoring

    def _decode_training_tables(self) -> _TrainingTables:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        team_rows: tuple[TeamTraining, ...] = ()
        group_rows: tuple[MentoringGroup, ...] = ()
        training_stats = unmanaged_training_stats()
        # One game_db borrow covers the managed club, the club records and the players, so a
        # cold call decompresses that section once rather than once per reader. The managed
        # club is read inside it and not before it, because that reader reads game_db too.
        with context.section(GAME_DB_SECTION) as game_db:
            game_db_length = len(game_db)
            # Whether the save lists a club for its manager decides whether there is anything
            # to read: the section holds one calendar per team of that club and nothing else.
            managed_clubs = self.managed_clubs()
            if len(managed_clubs) > 0:
                managed_club_uid = managed_clubs[0].club_uid
                # Every row carries a club name and every member a player name, so both tables
                # are read through the readers that enforce their own checks rather than through
                # the indexes behind them: forcing those bounds to something unmeetable must
                # stop this call instead of leaving it handing out names from indexes whose
                # checks never ran.
                self.clubs()
                players = self.players()
                club_index = context.club_index()
                player_records = context.player_records()
                managed_club = club_index.club_by_uid.get(managed_club_uid)
                club_team_ids = frozenset(
                    () if managed_club is None else (team.team_id for team in managed_club.teams)
                )
                layout = find_training_layout(
                    save_info.section_schemas.get(TRAINING_SECTION), save_info.build
                )
                with context.section(TRAINING_SECTION) as training:
                    blocks, walk_counts = walk_training_blocks(
                        training, club_team_ids, layout, save_info.file_name
                    )
                    library = locate_schedule_library(training, walk_counts.blocks_end, layout)
                team_rows, group_rows, training_stats = build_training_tables(
                    blocks,
                    library,
                    club_index,
                    player_records,
                    players,
                    managed_club_uid,
                    walk_counts,
                )
        # Both checks run before either table is built: when one fails, nothing is cached and
        # the next call walks and checks again.
        reader_checks = (
            _checks.check_training(training_stats, gate_bounds, game_db_length),
            _checks.check_mentoring(training_stats, gate_bounds, game_db_length),
        )
        self._enforce_checks(reader_checks)
        return _TrainingTables(
            Table(team_rows, TeamTraining), Table(group_rows, MentoringGroup), reader_checks
        )

    def _reader_check(self, reader_name: str) -> ReaderCheck | None:
        """The checks a reader passed when its table was read, or None before it was read."""
        stored = self._context.cached_value(_check_cache_key(reader_name))
        return stored if isinstance(stored, ReaderCheck) else None

    def _shared_pass_cached(self, pass_name: str) -> bool:
        """Whether the decode the readers of a pass share has finished and been kept.

        A failure raised before it finished is a failure of the pass: every other reader of
        that pass would run the same decode again only to raise the same error, which for the
        span means streaming it once per reader. A failure raised after it was kept is the
        reader's own, and the rest of the pass still has its own work to do.
        """
        cache_key = _SHARED_PASS_CACHE_KEYS.get(pass_name)
        if cache_key is None:
            return False
        return self._context.cached_value(cache_key) is not None

    def _gate_bounds(self) -> GateBounds:
        save_info = self._context.info
        return find_layout(
            GateBounds,
            GAME_DB_SECTION,
            save_info.section_schemas.get(GAME_DB_SECTION),
            save_info.build,
        ).layout

    def _enforce(self, reader_name: str, results: Sequence[GateResult]) -> None:
        """Report this reader's failed checks: raise on a strict save, else warn at most once.

        Raises:
            ReaderCheckError: An applied check failed and the save was opened strict.
        """
        if self._strict:
            _checks.enforce(reader_name, results, strict=True)
            return
        if reader_name in self._warned_readers:
            return
        if _checks.enforce(reader_name, results, strict=False):
            self._warned_readers.add(reader_name)

    def _enforce_checks(self, reader_checks: Sequence[ReaderCheck]) -> None:
        """Report these readers' failed checks: raise on a strict save, else warn at most once.

        A reader warned about once is not warned about again, so a table read a second time,
        and an index two readers both check, cost one warning between them rather than one
        each. The first failure a reader reports is therefore the one its caller hears about;
        `fmsave.validate_save` lists every check of every reader.

        Raises:
            ReaderCheckError: An applied check failed and the save was opened strict.
        """
        if self._strict:
            _checks.enforce_checks(reader_checks, strict=True)
            return
        unwarned = tuple(
            reader_check
            for reader_check in reader_checks
            if reader_check.reader not in self._warned_readers
        )
        if _checks.enforce_checks(unwarned, strict=False):
            self._warned_readers.update(reader_check.reader for reader_check in unwarned)

    def _store_reader_checks(self, reader_checks: Sequence[ReaderCheck]) -> None:
        """Keep each reader's checks next to its table, for the validation report."""
        context = self._context
        for reader_check in reader_checks:
            context.cached(_check_cache_key(reader_check.reader), _returning(reader_check))

    def _read_clubs(self) -> Table[Club]:
        gate_bounds = self._gate_bounds()
        club_index = self._context.club_index()
        club_check = _checks.check_clubs(club_index.stats, gate_bounds, club_index.game_db_bytes)
        self._enforce_checks((club_check,))
        self._store_reader_checks((club_check,))
        return Table(club_index.clubs, Club)

    def _read_managed_clubs(self) -> Table[ManagedClub]:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so contract "
                "chain records cannot be decoded"
            )
        layouts = find_managed_club_layouts(save_info.section_schemas, save_info.build)
        gate_bounds = self._gate_bounds()
        with (
            context.section(HUMANS_SECTION) as humans,
            context.section(SAVE_SUMMARY_SECTION) as summary,
            context.section(GAME_DB_SECTION) as game_db,
        ):
            club_index = context.club_index()
            managed_clubs, managed_stats = resolve_managed_clubs(
                humans, game_db, summary, club_index, clock, layouts, save_info.file_name
            )
            game_db_length = len(game_db)
        managed_check = _checks.check_managed(managed_stats, gate_bounds, game_db_length)
        self._enforce_checks((managed_check,))
        self._store_reader_checks((managed_check,))
        return Table(managed_clubs, ManagedClub)

    def _read_stages(self) -> Table[Stage]:
        context = self._context
        gate_bounds = self._gate_bounds()
        # With a name map the competitions are read first, checks and all. Every name a stage
        # row carries comes out of the competition index, so that index must have passed its
        # own checks before a name of its leaves this reader: a build that mis-paired entity
        # ids with database ids would otherwise put another competition's name on every stage
        # row and raise nothing at all. Reading the competition table runs those checks, and it
        # builds the stage index inside its own game_db borrow, so both indexes still come out
        # of a single decompression. Without a map every competition_name would be None anyway,
        # so the stage index is read on its own and the id-pair pass that names competitions is
        # never paid for. Either way this reader needs no part of game_db beyond the cached
        # indexes, so a warm call decompresses nothing.
        name_for: Callable[[int | None], str | None] | None = None
        if context.competition_names:
            self.competitions()
            name_for = context.competition_index().name_for
        stage_index = context.stage_index()
        stage_check = _checks.check_stages(
            stage_index.stats, gate_bounds, stage_index.game_db_bytes
        )
        self._enforce_checks((stage_check,))
        self._store_reader_checks((stage_check,))
        stages = stage_index.stages
        return Table(stages if name_for is None else named_stages(stages, name_for), Stage)

    def _read_competitions(self) -> Table[Competition]:
        context = self._context
        gate_bounds = self._gate_bounds()
        competition_index = context.competition_index()
        # The stage index the competitions were built from is cached by the call above and
        # already carries the section length the checks want, so game_db is read once in all.
        game_db_length = context.stage_index().game_db_bytes
        competition_check = _checks.check_competitions(
            competition_index.stats, gate_bounds, game_db_length
        )
        self._enforce_checks((competition_check,))
        self._store_reader_checks((competition_check,))
        return Table(competition_index.competitions, Competition)

    def _read_transfer_windows(self) -> Table[TransferWindow]:
        context = self._context
        save_info = context.info
        gate_bounds = self._gate_bounds()
        tagged_layout, window_layout = find_transfer_window_layouts(
            save_info.section_schemas.get(GAME_DB_SECTION), save_info.build
        )
        with context.section(GAME_DB_SECTION) as game_db:
            windows, window_stats = read_transfer_windows(game_db, tagged_layout, window_layout)
            game_db_length = len(game_db)
        window_check = _checks.check_transfer_windows(window_stats, gate_bounds, game_db_length)
        self._enforce_checks((window_check,))
        self._store_reader_checks((window_check,))
        return Table(windows, TransferWindow)

    def _players_table_entry_point(self) -> Table[Player]:
        tables = self._decode_player_tables()
        context = self._context
        self._store_reader_checks(tables.reader_checks)
        context.cached(CONTRACTS_TABLE_CACHE_KEY, lambda: tables.contracts)
        context.cached(SUSPENSIONS_TABLE_CACHE_KEY, lambda: tables.suspensions)
        return tables.players

    def _contracts_table_entry_point(self) -> Table[Contract]:
        tables = self._decode_player_tables()
        context = self._context
        self._store_reader_checks(tables.reader_checks)
        context.cached(PLAYERS_TABLE_CACHE_KEY, lambda: tables.players)
        context.cached(SUSPENSIONS_TABLE_CACHE_KEY, lambda: tables.suspensions)
        return tables.contracts

    def _suspensions_table_entry_point(self) -> Table[Suspension]:
        tables = self._decode_player_tables()
        context = self._context
        self._store_reader_checks(tables.reader_checks)
        context.cached(PLAYERS_TABLE_CACHE_KEY, lambda: tables.players)
        context.cached(CONTRACTS_TABLE_CACHE_KEY, lambda: tables.contracts)
        return tables.suspensions

    def _decode_player_tables(self) -> _PlayerTables:
        context = self._context
        save_info = context.info
        clock = save_info.game_date
        if clock is None:
            raise ReaderCheckError(
                f"{save_info.file_name}: the save's in-game date is unreadable, so person "
                "blocks and ages cannot be decoded"
            )
        game_db_schema = save_info.section_schemas.get(GAME_DB_SECTION)
        gate_bounds = self._gate_bounds()
        with context.section(GAME_DB_SECTION) as game_db:
            club_index = context.club_index()
            player_records = context.player_records()
            name_pools = context.name_pools()
            person_layout = find_layout(
                PersonBlockLayout, GAME_DB_SECTION, game_db_schema, save_info.build
            ).layout
            contract_layout = find_layout(
                ContractLayout, GAME_DB_SECTION, game_db_schema, save_info.build
            ).layout
            suspension_layout = find_layout(
                SuspensionLayout, GAME_DB_SECTION, game_db_schema, save_info.build
            ).layout
            decoder = build_player_decoder(
                player_records.layout,
                club_index,
                name_pools,
                clock,
                person_layout,
                contract_layout,
                save_info.file_name,
            )
            suspension_entries_by_position = locate_suspensions(
                game_db, player_records, suspension_layout
            )
            # With a name map the competitions are read first, checks and all. Every
            # competition name a ban carries comes out of the competition index, so that index
            # must have passed its own checks before a name of its leaves this reader: a build
            # that mis-paired entity ids with database ids would otherwise name every ban
            # after another competition and raise nothing at all. Reading the competition
            # table runs those checks inside this same borrow, so game_db is still
            # decompressed once. Without a map every competition_name is None anyway, so
            # nothing is read on its account.
            if context.competition_names:
                self.competitions()
                suspension_entries_by_position = named_entries(
                    suspension_entries_by_position, context.competition_index().name_for
                )
            no_suspension_entries: tuple[SuspensionEntry, ...] = ()
            suspension_entries_for = suspension_entries_by_position.get
            history_layout = find_history_layout(save_info.build)
            history_selectors: dict[int, int] = {}
            decoded_players: list[Player] = []
            decoded_contracts: list[Contract] = []
            decoded_suspensions: list[Suspension] = []
            append_player = decoded_players.append
            append_contract = decoded_contracts.append
            extend_suspensions = decoded_suspensions.extend
            record_offsets = player_records.record_offsets
            game_db_length = len(game_db)
            last_position = len(record_offsets) - 1
            for position, record_offset in enumerate(record_offsets):
                record_window_end = window_end(player_records, position, game_db_length)
                suspension_entries = suspension_entries_for(position, no_suspension_entries)
                player, contract = decoder.decode(
                    game_db,
                    record_offset,
                    record_window_end,
                    is_last_record=position == last_position,
                    suspension_entries=suspension_entries,
                )
                history_selectors[player.uid] = history_selector(
                    game_db,
                    decoder.person_decoder.last_block_start,
                    record_offset,
                    record_window_end,
                    history_layout,
                )
                append_player(player)
                if contract is not None:
                    append_contract(contract)
                if suspension_entries:
                    extend_suspensions(suspension_rows(player, suspension_entries))
        # All records are decoded above. Every check of the pass runs here, before any table is
        # built: when one fails, nothing is cached and the next call decodes and checks again.
        player_count = len(decoded_players)
        reader_checks = (
            _checks.check_players(
                collect_player_stats(
                    decoded_players, decoder, player_records.markerless_count, gate_bounds
                ),
                gate_bounds,
                game_db_length,
            ),
            _checks.check_contracts(
                decoder.contract_decoder.stats(player_count, len(decoded_contracts)),
                gate_bounds,
                game_db_length,
            ),
            _checks.check_suspensions(
                suspension_stats(suspension_entries_by_position, player_count, clock),
                gate_bounds,
                game_db_length,
            ),
        )
        self._enforce_checks(reader_checks)
        context.cached(HISTORY_SELECTORS_CACHE_KEY, lambda: FrozenMapping(history_selectors))
        return _PlayerTables(
            Table(tuple(decoded_players), Player),
            Table(tuple(decoded_contracts), Contract),
            Table(tuple(decoded_suspensions), Suspension),
            reader_checks,
        )

    def close(self) -> None:
        """Close the save and release its cached results.

        Calling a reader afterwards raises SaveClosedError; tables already returned keep working.
        """
        self._context.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "closed" if self.closed else "open"
        return f"<fmsave.Save {self._info.game} {self._info.build} {state}>"

    def _require_open(self) -> ContainerIndex:
        if self.closed:
            raise closed_save_error()
        return self._container_index

    def _read_section(self, name: str) -> bytes:
        """Read one whole section; readers borrow sections through SaveContext.section instead.

        Meant for the small sections read when the save is opened.
        """
        return read_section(self._require_open(), name)


def open_save(
    path: str | os.PathLike[str],
    *,
    strict: bool = False,
    competition_names: Mapping[int, str] | str | os.PathLike[str] | None = None,
) -> Save:
    """Open a Football Manager 26 save file for reading.

    Args:
        path: The save file to read.
        strict: Whether a failed reader check stops the reader. The checks are bounds measured
            on a handful of saves, so a save stranger than those is read and warned about by
            default: a reader whose checks fail issues `ReaderCheckWarning` and hands its table
            back. With True it raises `ReaderCheckError` instead, which is what a pipeline that
            would rather stop than read a table it cannot vouch for wants. A structural failure,
            where the decode has no table to hand back, raises either way.
        competition_names: Names for competitions, keyed on `Competition.database_id`, either
            as a mapping or as the path of a two-column CSV that
            `fmsave.read_competition_names` reads. No save stores a competition name and fmsave
            ships none, so without this every `Competition.name` and every denormalised
            `competition_name` is None. Tables are read once and then kept, so the map cannot be
            changed afterwards: open the save again to read it under a different one.

    Raises:
        FileNotFoundError: The file does not exist.
        NotAFmSaveError: The file is not a Football Manager save.
        CorruptSaveError: The save is damaged or was being written.
        UnsupportedGameError: The save is from another Football Manager version.
        ReaderCheckError: The save metadata does not match the expected layout.
        OSError: A competition name CSV cannot be opened or read.
        TypeError: A competition name mapping holds a key that is not an int, or a name that is
            not a str.
        ValueError: A competition name CSV is malformed, or a supplied name is empty.

    Warns:
        UnknownBuildWarning: The save comes from an FM26 build without layout tables.
    """
    # The map is checked before the file is touched, so a mistake in it costs none of the work
    # of opening a save.
    names = _normalized_competition_names(competition_names)
    container_index = read_index(path)
    return Save(
        container_index,
        read_save_info(container_index),
        strict=strict,
        competition_names=names,
    )
