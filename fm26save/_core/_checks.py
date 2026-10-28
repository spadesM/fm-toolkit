"""Private reader checks, and the validation report built from them.

`fmsave.checks` is the public face of this module; nothing here but the names it re-exports is
part of fmsave's API.

While a reader decodes, it counts what it sees into a stats record from `fmsave._reader_stats`
(`PlayerStats`, `ContractStats`, `ClubStats`, `SuspensionStats`, `ManagedStats`, `StageStats`,
`CompetitionStats`, `FixtureStats`, `TransferWindowStats`, `LeagueTableStats`, `RulesStats`,
`MatchStats`, `StadiumStats`, `FinanceStats`, `FacilityStats`, `AffiliateStats`,
`JobVacancyStats`, `StaffStats`, `InjuryTypeStats`, `InjuryStats`, `TrainingStats` or
`TacticStats`).
The `evaluate_*` functions compare those counts with the loose `GateBounds` registered for the
save's layout and return one `GateResult` per check, and `enforce` reports an applied check
that failed, before the reader caches its table: it raises `GateCheckError` on a save opened
with `strict=True`, and otherwise warns `ReaderCheckWarning` with the same message and lets the
reader hand its table back. A bound is a measurement of the saves it was drawn from and no
more, so a save unlike those is not a save fmsave should refuse to read. What still raises is a
structural failure, which readers raise for themselves: a decode with no table to hand back.
The checks apply only to a `game_db` of at least `GateBounds.minimum_applies_from_bytes`, since
smaller sections come from fragments that cannot meet full-save counts.

`validate_save` runs every reader and returns a `ValidationReport`, which holds only structural
facts, counts and rates: never names, uids or other values from the save.
"""

from __future__ import annotations

import os.path
import platform
import warnings
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from statistics import median_low
from typing import TYPE_CHECKING, Literal

from fm26save._core._context import closed_save_error
from fm26save._core._errors import ISSUES_URL, FmsaveError, ReaderCheckError, ReaderCheckWarning
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import BoundPair, GateBounds
from fm26save._core._package import __version__
from fm26save._core._reader_stats import (
    AffiliateStats,
    ClubStats,
    CompetitionStats,
    ContractStats,
    FacilityStats,
    FinanceStats,
    FixtureStats,
    InjuryStats,
    InjuryTypeStats,
    JobVacancyStats,
    LeagueTableStats,
    ManagedStats,
    MatchStats,
    PlayerStats,
    ResultStats,
    RulesStats,
    SeasonHistoryStats,
    SeasonStatsStats,
    StadiumStats,
    StaffStats,
    StageStats,
    SuspensionStats,
    TacticStats,
    TrainingStats,
    TransferWindowStats,
)
from fm26save._core._status import registered_statuses

if TYPE_CHECKING:
    from fm26save._core._save import Save


# Internal switch: when False, failed checks are still evaluated and reported, but neither
# raised nor warned about.
_gates_enabled = True


@contextmanager
def _gates_disabled() -> Generator[None]:
    """Evaluate and report checks without raising or warning inside the block, then restore it."""
    global _gates_enabled
    previous_setting = _gates_enabled
    _gates_enabled = False
    try:
        yield
    finally:
        _gates_enabled = previous_setting


CLUBS_READER = "clubs"
PLAYERS_READER = "players"
CONTRACTS_READER = "contracts"
SUSPENSIONS_READER = "suspensions"
MANAGED_CLUBS_READER = "managed_clubs"
STAGES_READER = "stages"
COMPETITIONS_READER = "competitions"
FIXTURES_READER = "fixtures"
TRANSFER_WINDOWS_READER = "transfer_windows"
LEAGUE_TABLES_READER = "league_tables"
COMPETITION_RULES_READER = "competition_rules"
PLAYER_MATCH_STATS_READER = "player_match_stats"
SEASON_HISTORY_READER = "player_season_history"
SEASON_STATS_READER = "player_season_stats"
INJURY_TYPES_READER = "injury_types"
INJURIES_READER = "injuries"
FINANCES_READER = "finances"
SPONSORSHIPS_READER = "sponsorships"
FACILITIES_READER = "facilities"
AFFILIATES_READER = "affiliates"
JOB_VACANCIES_READER = "job_vacancies"
STADIUMS_READER = "stadiums"
STAFF_READER = "staff"
STAFF_LISTS_READER = "staff_lists"
TACTICS_READER = "tactics"
SET_PIECES_READER = "set_pieces"
TRAINING_READER = "training"
MENTORING_READER = "mentoring"

# Several readers are built from one decode. A reader whose shared decode did not finish would
# have every other reader of the same pass redo that decode only to fail the same way, so the
# first failure is carried to the rest of the pass instead of being raised again.
PLAYER_PASS = "player"
SPAN_PASS = "span"
FINANCE_PASS = "finance"
STAFF_PASS = "staff"
TACTICS_PASS = "tactics"
TRAINING_PASS = "training"
# Players, contracts and suspensions are decoded in one pass, so they fail or succeed together.
_PLAYER_PASS_READERS = frozenset({PLAYERS_READER, CONTRACTS_READER, SUSPENSIONS_READER})
# Fixtures, league tables and competition rules read one streamed pass over the unnamed span,
# which is far the most expensive read fmsave makes. Stadiums join the pass because the home
# clubs of a ground are counted from the fixture calendar: a stadium read after that pass
# failed would stream the whole span a second time only to raise the same error.
_SPAN_PASS_READERS = frozenset(
    {FIXTURES_READER, LEAGUE_TABLES_READER, COMPETITION_RULES_READER, STADIUMS_READER}
)
# The months and the sponsors come out of one pass over the club records, so they fail or
# succeed together.
_FINANCE_PASS_READERS = frozenset({FINANCES_READER, SPONSORSHIPS_READER})
# The staff rows and the club staff lists come out of one pass over the club records and one
# over the whole section, so they fail or succeed together.
_STAFF_PASS_READERS = frozenset({STAFF_READER, STAFF_LISTS_READER})
# The tactics and the set-piece routines come out of one walk over the manager's team blocks,
# so they fail or succeed together.
_TACTICS_PASS_READERS = frozenset({TACTICS_READER, SET_PIECES_READER})
# The calendars and the mentoring groups come out of one walk over the training section, so
# they fail or succeed together.
_TRAINING_PASS_READERS = frozenset({TRAINING_READER, MENTORING_READER})
_READER_PASSES: FrozenMapping[str, str] = FrozenMapping(
    {
        **dict.fromkeys(_PLAYER_PASS_READERS, PLAYER_PASS),
        **dict.fromkeys(_SPAN_PASS_READERS, SPAN_PASS),
        **dict.fromkeys(_FINANCE_PASS_READERS, FINANCE_PASS),
        **dict.fromkeys(_STAFF_PASS_READERS, STAFF_PASS),
        **dict.fromkeys(_TACTICS_PASS_READERS, TACTICS_PASS),
        **dict.fromkeys(_TRAINING_PASS_READERS, TRAINING_PASS),
    }
)

_REPORT_REQUEST = f"Please report it at {ISSUES_URL} with the output of fmsave validate."
_NO_ANOMALIES: FrozenMapping[str, int] = FrozenMapping({})
_NO_COVERAGE: FrozenMapping[str, float] = FrozenMapping({})

# The one likely cause of each check whose failure has one, added to the failure message so a
# report names something a reader can act on. The text carries no digits, so a message still
# holds nothing but rounded rates and bounds.
_LIKELY_CAUSES: FrozenMapping[str, str] = FrozenMapping(
    {
        "tails_without_clause_table": "an unrecognised bonus list shape in the contract tail",
        "suspension_share_of_players": "a suspension entry layout that has moved",
        "suspension_scopes_known": "suspension scope codes this build no longer uses",
        "sponsor_clubs_minimum": (
            "a finance chain locator that found nothing, since a sponsor run is only looked "
            "for behind a club's own chain"
        ),
    }
)


@dataclass(frozen=True, slots=True)
class GateResult:
    """One reader check: an observed count or rate compared with its bounds.

    Attributes:
        name: The check's name.
        observed: The observed count, rate or median, or None when a rate has no denominator.
        minimum: The lowest value that passes, or None when there is no lower bound.
        maximum: The highest value that passes, or None when there is no upper bound.
        passed: Whether the check passed; a check that was not applied always passes.
        applied: Whether the check applied: False when `game_db` is too small for full-save
            counts.
    """

    name: str
    observed: float | None
    minimum: float | None
    maximum: float | None
    passed: bool
    applied: bool

    def to_json_dict(self) -> dict[str, object]:
        """The check as a JSON-ready dict."""
        return {
            "name": self.name,
            "observed": self.observed,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "passed": self.passed,
            "applied": self.applied,
        }


@dataclass(frozen=True, slots=True)
class ReaderCheck:
    """One reader's evaluated checks, its record count and its anomaly counts.

    It is what a `GateCheckError` carries, so a caller can read a failure from its numbers
    rather than from the message text.

    Attributes:
        reader: The reader the checks belong to, named as `ReaderValidation.reader` names it.
        record_count: How many records the reader decoded.
        gates: The reader's checks, in a fixed order; empty when it has none of its own.
        anomalies: Counts of records the reader decoded but flags, such as unresolved teams.
    """

    reader: str
    record_count: int
    gates: tuple[GateResult, ...]
    anomalies: Mapping[str, int]


class GateCheckError(ReaderCheckError):
    """A ReaderCheckError from failed reader checks, carrying every check of the failed pass.

    This is what `fmsave.open(..., strict=True)` raises when an applied check misses its
    bounds. Catching `ReaderCheckError` catches it, and `checks` holds the gate names, the
    observed values and the bounds the message rounds, so nothing has to be parsed back out of
    the text. A `ReaderCheckError` raised for any other reason carries no checks.

    Attributes:
        checks: Every reader of the failed pass, each with its own gates.
    """

    checks: tuple[ReaderCheck, ...]

    def __init__(self, message: str, checks: tuple[ReaderCheck, ...] = ()) -> None:
        super().__init__(message)
        self.checks = checks


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _gate(name: str, observed: float | None, bound: BoundPair, applied: bool) -> GateResult:
    minimum, maximum = bound
    if not applied:
        return GateResult(name, observed, minimum, maximum, passed=True, applied=False)
    passed = (
        observed is not None
        and (minimum is None or observed >= minimum)
        and (maximum is None or observed <= maximum)
    )
    return GateResult(name, observed, minimum, maximum, passed=passed, applied=True)


def _share_gate(
    name: str, numerator: int, denominator: int, bound: BoundPair, applied: bool
) -> GateResult:
    """A share check that judges nothing when its population is empty.

    Some populations can legitimately hold nothing: a table of grounds no club owns, a career
    whose calendar gives no club a home ground, a calendar whose records store no ground at
    all. A share with no denominator is then a fact about the save rather than a layout that
    has moved, so the check is reported as not applied instead of failing for want of a rate.
    A check used this way always sits beside a count check that does fail when a decode found
    nothing, so an empty population never hides a broken locator.
    """
    return _gate(name, _rate(numerator, denominator), bound, applied and denominator > 0)


def _applies(bounds: GateBounds, game_db_bytes: int) -> bool:
    return game_db_bytes >= bounds.minimum_applies_from_bytes


def _span_applies(bounds: GateBounds, span_bytes: int) -> bool:
    """Whether checks on what the span pass read apply: the span has its own size threshold."""
    return span_bytes >= bounds.span_minimum_applies_from_bytes


def evaluate_players(
    stats: PlayerStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The player reader's checks, in a fixed order."""
    applied = _applies(bounds, game_db_bytes)
    records = stats.records
    ages = stats.ages
    age_median = median_low(ages) if ages else None
    return (
        _gate("players_minimum", records, bounds.players_minimum, applied),
        _gate(
            "person_blocks",
            _rate(stats.with_person_block, records),
            bounds.person_blocks,
            applied,
        ),
        _gate(
            "names_resolved",
            _rate(stats.with_resolved_name, stats.with_person_block),
            bounds.names_resolved,
            applied,
        ),
        _gate(
            "relation_sentinel",
            _rate(stats.relation_sentinel_ok, stats.relation_entries),
            bounds.relation_sentinel,
            applied,
        ),
        _gate(
            "second_nation_qualifier",
            _rate(stats.second_nation_qualifier_ok, stats.second_nation_entries),
            bounds.second_nation_qualifier,
            applied,
        ),
        _gate(
            "handling_above_finishing",
            _rate(stats.handling_above_finishing, records),
            bounds.handling_above_finishing,
            applied,
        ),
        _gate(
            "outfield_goalkeeper_block_low",
            _rate(stats.outfield_goalkeeper_block_low, stats.outfield_players),
            bounds.outfield_goalkeeper_block_low,
            applied,
        ),
        _gate(
            "with_natural_position",
            _rate(stats.with_natural_position, records),
            bounds.with_natural_position,
            applied,
        ),
        _gate(
            "height_in_range",
            _rate(stats.height_in_range, records),
            bounds.height_in_range,
            applied,
        ),
        _gate("height_median", stats.heights_median, bounds.height_median, applied),
        _gate("age_median", age_median, bounds.age_median, applied),
        _gate(
            "aged_in_range", _rate(stats.aged_in_range, len(ages)), bounds.aged_in_range, applied
        ),
        _gate(
            "condition_sharpness_in_range",
            _rate(stats.condition_sharpness_in_range, records),
            bounds.condition_sharpness_in_range,
            applied,
        ),
        _gate(
            "join_date_valid",
            _rate(stats.with_valid_join_date, records),
            bounds.join_date_valid,
            applied,
        ),
        _gate(
            "world_not_above_current",
            _rate(stats.world_not_above_current, records),
            bounds.world_not_above_current,
            applied,
        ),
        _gate(
            "home_near_current",
            _rate(stats.home_near_current, records),
            bounds.home_near_current,
            applied,
        ),
        _gate(
            "team_resolved",
            _rate(stats.team_resolved, stats.with_team),
            bounds.team_resolved,
            applied,
        ),
        _gate(
            "home_grown_club_refs_resolved",
            _rate(stats.home_grown_club_refs_resolved, stats.home_grown_club_refs),
            bounds.home_grown_club_refs_resolved,
            applied,
        ),
    )


def evaluate_contracts(
    stats: ContractStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The contract reader's checks, in a fixed order."""
    applied = _applies(bounds, game_db_bytes)
    return (
        _gate(
            "players_with_chain",
            _rate(stats.players_with_chain, stats.players),
            bounds.players_with_chain,
            applied,
        ),
        _gate(
            "no_contract_in_effect",
            _rate(stats.without_contract_in_effect, stats.players_with_chain),
            bounds.no_contract_in_effect,
            applied,
        ),
        _gate(
            "date_marked_chain_records",
            _rate(stats.date_marked_chain_records, stats.chain_records),
            bounds.date_marked_chain_records,
            applied,
        ),
        _gate(
            "tails_parsed",
            _rate(stats.tails_parsed, stats.chain_records),
            bounds.tails_parsed,
            applied,
        ),
        _gate(
            "tails_without_clause_table",
            _rate(stats.tails_without_clause_table, stats.tails_parsed),
            bounds.tails_without_clause_table,
            applied,
        ),
        _gate(
            "clause_terminator",
            _rate(stats.clause_tables_ending_at_tail, stats.clause_tables),
            bounds.clause_terminator,
            applied,
        ),
        _gate(
            "contract_head",
            _rate(stats.head_ok, stats.clause_tables),
            bounds.contract_head,
            applied,
        ),
        _gate(
            "past_dated_tail_ends",
            _rate(stats.tail_ends_past, stats.tail_ends),
            bounds.past_dated_tail_ends,
            applied,
        ),
        _gate(
            "chain_teams_resolved",
            _rate(stats.chain_teams_resolved, stats.chain_records),
            bounds.chain_teams_resolved,
            applied,
        ),
    )


def evaluate_clubs(
    stats: ClubStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The club reader's checks, in a fixed order."""
    applied = _applies(bounds, game_db_bytes)
    records = stats.records
    return (
        _gate("clubs_minimum", records, bounds.clubs_minimum, applied),
        _gate(
            "team_lists_found",
            _rate(stats.team_lists_found, records),
            bounds.team_lists_found,
            applied,
        ),
        _gate("status_normal", _rate(stats.status_normal, records), bounds.status_normal, applied),
        _gate(
            "status_confirmation",
            _rate(stats.status_confirmed, stats.status_normal),
            bounds.status_confirmation,
            applied,
        ),
        _gate(
            "affiliate_lists_found",
            _rate(stats.affiliate_lists, records),
            bounds.affiliate_lists_found,
            applied,
        ),
        _gate(
            "affiliate_teams_linked",
            _rate(stats.affiliate_refs_linked, stats.affiliate_refs),
            bounds.affiliate_teams_linked,
            applied and stats.affiliate_refs > 0,
        ),
        _gate(
            "reputation_found",
            _rate(stats.reputation_found, records),
            bounds.reputation_found,
            applied,
        ),
        _gate("reputation_median", stats.reputations_median, bounds.reputation_median, applied),
    )


def evaluate_suspensions(
    stats: SuspensionStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The suspension reader's checks, in a fixed order.

    The first two apply whenever the section is large enough, including when the search found
    no entry at all: an empty result scores below the share's lower bound and leaves the clock
    check with no rate, so an entry layout that has moved fails here rather than reporting a
    save whose players are never banned. The scope check judges what the entries that were
    found say rather than how many there are, so it is not applied when there are none and
    the first check is what fails then.

    `issued_after_clock` judges the bans covering ONE COMPETITION alone. A ban covering a
    whole nation carries a date ahead of the in-game date as ordinary career state, so over
    every entry this check rises and falls with a career's own fixture list and fired on a
    save whose decode was sound. Over the competition-scope entries it reads zero on every
    save state measured, which makes it a tighter check than the one it replaces: a date read
    from neighbouring bytes moves far more than a percent of them past the clock.
    """
    applied = _applies(bounds, game_db_bytes)
    return (
        _gate(
            "suspension_share_of_players",
            _rate(stats.players_with_entries, stats.players),
            bounds.suspension_share_of_players,
            applied,
        ),
        _gate(
            "issued_after_clock",
            _rate(stats.competition_issued_after_clock, stats.competition_entries),
            bounds.issued_after_clock,
            applied,
        ),
        _share_gate(
            "suspension_scopes_known",
            stats.entries_with_known_scope,
            stats.entries,
            bounds.suspension_scopes_known,
            applied,
        ),
    )


def evaluate_stages(
    stats: StageStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The stage reader's checks, in a fixed order."""
    applied = _applies(bounds, game_db_bytes)
    rows = stats.rows
    return (
        _gate("stage_rows_minimum", rows, bounds.stage_rows_minimum, applied),
        _gate("stage_walk_gaps", stats.gaps, bounds.stage_walk_gaps, applied),
        _gate(
            "stage_ids_ascending",
            _rate(stats.ascending_steps, stats.steps),
            bounds.stage_ids_ascending,
            applied,
        ),
        _gate(
            "stage_rows_with_competition",
            _rate(stats.with_competition, rows),
            bounds.stage_rows_with_competition,
            applied,
        ),
        _gate(
            "stage_trailing_sentinel",
            _rate(stats.trailing_sentinel_ok, rows),
            bounds.stage_trailing_sentinel,
            applied,
        ),
        _gate(
            "stage_table_tail_bytes",
            stats.bytes_after_table,
            bounds.stage_table_tail_bytes,
            applied,
        ),
    )


def evaluate_competitions(
    stats: CompetitionStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The competition reader's checks, in a fixed order.

    Nothing bounds how many competitions are named from below: no save stores a competition
    name, so that share is zero until a reader supplies a name map, and zero is not a fault.
    What is checked is that no name reached a competition the save gives no database id, since
    the map is keyed on that id alone. A competition two competitions' records claim, or whose
    database id another competition also claims, is left without one and must stay unnamed;
    naming it anyway would put a different competition's name on it.
    """
    applied = _applies(bounds, game_db_bytes)
    competitions = stats.competitions
    return (
        _gate("competitions_minimum", competitions, bounds.competitions_minimum, applied),
        _gate(
            "competition_database_ids_mapped",
            _rate(stats.with_database_id, competitions),
            bounds.competition_database_ids_mapped,
            applied,
        ),
        _gate(
            "competition_database_id_conflicts",
            _rate(stats.database_id_conflicts, competitions),
            bounds.competition_database_id_conflicts,
            applied,
        ),
        _gate(
            "competition_names_within_database_ids",
            _rate(stats.with_name, stats.with_database_id),
            bounds.competition_names_within_database_ids,
            applied,
        ),
    )


def evaluate_fixtures(
    stats: FixtureStats, bounds: GateBounds, span_bytes: int
) -> tuple[GateResult, ...]:
    """The fixture reader's checks, in a fixed order.

    These judge what one pass over the span read, not `game_db`, so they apply from the span's
    own size threshold. The first five apply whenever the span is large enough, including when
    the pass found no fixture at all: an empty calendar scores below the record floor and the
    stray floor and leaves the three shares without a denominator, so a calendar locator that
    has moved fails here rather than reporting a career with no matches.

    `fixture_stadiums_resolved` is the one exception, because a calendar legitimately holds
    records that store no ground: it applies only when some record stores one. A calendar that
    stored none at all would fail the record floor first.

    `fixture_cluster_share` and `fixture_strays_minimum` bound the same split from opposite
    sides. The share falls when the run separating the calendar from its stray copies is too
    eager and the calendar shatters. The stray floor catches the other way that rule can
    break, a separation so slack that nothing is told apart at all: every record then counts
    as the calendar, which puts the template matches no save plays on every career, and the
    share cannot see it, because a reader keeping every stray copy scores a perfect 1.0.
    """
    applied = _span_applies(bounds, span_bytes)
    cluster_records = stats.cluster_records
    return (
        _gate("fixtures_minimum", cluster_records, bounds.fixtures_minimum, applied),
        _gate(
            "fixture_cluster_share",
            _rate(cluster_records, stats.span_records),
            bounds.fixture_cluster_share,
            applied,
        ),
        _gate(
            "fixture_strays_minimum",
            stats.span_records - cluster_records,
            bounds.fixture_strays_minimum,
            applied,
        ),
        _gate(
            "fixture_stage_resolved",
            _rate(stats.stage_resolved, stats.with_stage),
            bounds.fixture_stage_resolved,
            applied,
        ),
        _gate(
            "fixture_club_teams_resolved",
            _rate(
                stats.home_team_resolved + stats.away_team_resolved,
                2 * cluster_records - stats.stub_team_references,
            ),
            bounds.fixture_teams_resolved,
            applied and (cluster_records == 0 or 2 * cluster_records > stats.stub_team_references),
        ),
        _share_gate(
            "fixture_stadiums_resolved",
            stats.stadium_resolved,
            stats.with_stadium,
            bounds.fixture_stadiums_resolved,
            applied,
        ),
    )


def evaluate_results(
    stats: ResultStats, bounds: GateBounds, span_bytes: int
) -> tuple[GateResult, ...]:
    """The stage-keyed result checks, in a fixed order.

    These judge the same pass over the span the calendar's own checks do, so they apply from
    the span's size threshold. All three apply whenever the span is large enough, including
    when nothing was accepted at all: an empty result scores below the record floor and leaves
    both shares without a denominator, so a locator that has moved fails here rather than
    reporting a career whose matches were never scored.

    `results_joined` is what says the record is still being read correctly. The scores are found
    by one locator and the calendar they join by another, in a different region, so the two
    agree on a date and both team ids only if both are being decoded right; the same records
    joined on a key wrong by one day, or with the two sides swapped, joined nothing at all on
    every save measured. A decode that drifted would keep finding records and stop matching.

    `results_for_unplayed` is the tripwire for the opposite failure, a join loose enough to
    attach scores to matches the calendar says have not been played. That is wrong however many
    of them it finds, and no rate of joining can see it.
    """
    applied = _span_applies(bounds, span_bytes)
    accepted = stats.accepted
    return (
        _gate("result_records_minimum", accepted, bounds.result_records_minimum, applied),
        _gate("results_joined", _rate(stats.joined, accepted), bounds.results_joined, applied),
        _gate(
            "results_for_unplayed",
            _rate(stats.score_for_unplayed, stats.joined),
            bounds.results_for_unplayed,
            applied,
        ),
    )


def evaluate_transfer_windows(
    stats: TransferWindowStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The transfer-window reader's checks, in a fixed order.

    Both apply whenever the section is large enough, including when the walk decoded nothing:
    an empty result scores zero windows, which fails the count, and leaves the date share with
    no denominator at all, which fails for want of a rate rather than passing quietly. That is
    the point of the pair, since the tagged stream holds far more dated records than windows
    and a decode that has moved would otherwise look like a save that simply has none.
    """
    applied = _applies(bounds, game_db_bytes)
    windows = stats.windows
    return (
        _gate("transfer_windows_minimum", windows, bounds.transfer_windows_minimum, applied),
        _gate(
            "transfer_window_dates",
            _rate(windows, windows + stats.incomplete),
            bounds.transfer_window_dates,
            applied,
        ),
    )


def _calendar_meets_division_floor(stats: LeagueTableStats, bounds: GateBounds) -> bool:
    """Whether the calendar shows at least as many divisions under way as the floor asks."""
    floor = bounds.double_round_robin_divisions[0]
    return floor is None or stats.started_calendar_divisions >= floor


def evaluate_league_tables(
    stats: LeagueTableStats, bounds: GateBounds, span_bytes: int
) -> tuple[GateResult, ...]:
    """The league-table reader's checks, in a fixed order.

    These judge what one pass over the span read, so they apply from the span's own size
    threshold. The first four apply whenever the span is large enough, including when the pass
    found no block at all: an empty result scores below the block floor and the duplicate
    floor, and leaves the two shares without a denominator, so a table layout that has moved
    fails here rather than reporting a career with no tables. The division floor applies on
    the same terms once the fixture calendar shows at least that many divisions under way.

    `table_venue_calendar_agreement` is the exception, and is the check that keeps the slot
    parity honest. It compares the venue the slot's parity names against the venue the fixture
    calendar's own stored home team names, on the tables whose rows account for exactly one
    season of that calendar. Reading the parity the other way round drops it from about 0.998
    to about 0.002 on every save measured, so a parity chosen wrongly fails here. Its
    population is legitimately empty on a layout that settles no parity and on a career whose
    tables are all out of step with its calendar, so an empty population is reported rather
    than failed; the four count checks above are what fail when the table decode itself found
    nothing.

    Two of the five exist to catch a filter that stopped filtering, which no rate here can see.
    `table_block_duplicates_minimum` fails when the deduplication stops dropping the save's
    repeated copies of a block: the copies are sound blocks differing from the block they
    repeat only in undecoded head bytes, so they pass every other check, and left in they
    shatter the tables they sit in, turning about 800 tables into about 4,700 on the corpus.
    That floor is the only check that sees it, because every shattered piece is still shaped
    like a small table; the division count barely moves, so it is not a second tripwire for
    this failure and is not presented as one.
    `double_round_robin_divisions` guards the opposite failure, a grouping that runs tables
    together: a merged group holds clubs twice over and cannot keep a division's shape, so the
    count collapses. `table_groups_resolved` sees neither, since one enormous group scores a
    perfect 1.0 on it. A division keeps that shape only once every member has played, since a
    block with no match played is never kept, so in the weeks before the leagues a save holds
    start, the count is legitimately near zero. The floor therefore applies only when the
    calendar shows at least as many divisions under way (`started_calendar_divisions`) as the
    floor asks for; a merged grouping still fails it then, because the calendar's own count
    does not depend on how the blocks were grouped.

    `table_groups_resolved` observes near 1.0 on every save measured, which reads stronger than
    it is: 30% to 43% of tables hold a single block, and a one-block table meets the vote's
    half-the-members rule on a majority of one. Over the tables of two blocks or more the share
    is 0.998 to 1.000, so this gate is a floor under a near-saturated rate rather than a
    discriminating one.
    """
    applied = _span_applies(bounds, span_bytes)
    blocks = stats.blocks
    return (
        _gate("table_blocks_minimum", blocks, bounds.table_blocks_minimum, applied),
        _gate(
            "table_block_duplicates_minimum",
            stats.duplicate_blocks,
            bounds.table_block_duplicates_minimum,
            applied,
        ),
        _gate(
            "table_block_team_in_range",
            _rate(stats.team_id_in_range, blocks),
            bounds.table_block_team_in_range,
            applied,
        ),
        _gate(
            "table_groups_resolved",
            _rate(stats.groups_resolved, stats.groups),
            bounds.table_groups_resolved,
            applied,
        ),
        _gate(
            "double_round_robin_divisions",
            stats.double_round_robin_divisions,
            bounds.double_round_robin_divisions,
            applied and _calendar_meets_division_floor(stats, bounds),
        ),
        _share_gate(
            "table_venue_calendar_agreement",
            stats.venue_slots_agreeing,
            stats.venue_slots_decided,
            bounds.table_venue_calendar_agreement,
            applied,
        ),
    )


def evaluate_competition_rules(
    stats: RulesStats, bounds: GateBounds, span_bytes: int
) -> tuple[GateResult, ...]:
    """The competition-rules reader's checks, in a fixed order.

    These judge what one pass over the span read, so they apply from the span's own size
    threshold. The first two apply whenever the span is large enough, including when the pass
    found no block at all: an empty result scores no markers, which fails the count, and leaves
    the parsed share with no denominator, which fails for want of a rate rather than passing
    quietly. That is what a marker that has moved looks like from the counts, and it is why the
    share is not allowed to stand alone.

    `rules_fully_parsed` counts the strict sense of a parsed block: the promotion quad written
    twice identically **and** the tie-break list, the prize list and every round record
    decoded. A share measured without the quad sits about ten points higher, so this gate's
    bound is not comparable with one.

    The last two judge the positional competition link, and they fail on different faults.

    `rules_link_round_dates` is the share of a linked block's dated rounds that fall on a date
    the linked competition plays a fixture on. Its misalignment is taking the run of table
    blocks stored before a block rather than the run after it, which drops the share from 0.74
    to 0.78 down to 0.55 to 0.58 on the saves measured. It is a share with no population of
    its own to fall back on, so an empty link leaves it without a denominator and is reported
    rather than failed.

    `rules_linked_blocks_minimum` is the count that closes that hole, and it is a count on
    purpose: the misalignment above permutes the same runs among the same blocks, so **every
    share built from this link is invariant under it** -- the share of blocks that link at all
    is 0.55 to 0.68 whichever run is taken -- and only a count falls when the link stops
    linking. It applies above `rules_link_minimum_applies_from_runs` blocks with a run, so a
    save holding few divisions is not judged against a count measured on saves holding many.
    """
    applied = _span_applies(bounds, span_bytes)
    enough_runs = stats.blocks_with_run >= bounds.rules_link_minimum_applies_from_runs
    return (
        _gate("rules_markers_minimum", stats.markers, bounds.rules_markers_minimum, applied),
        _gate(
            "rules_fully_parsed",
            _rate(stats.fully_parsed, stats.blocks),
            bounds.rules_fully_parsed,
            applied,
        ),
        _gate(
            "rules_linked_blocks_minimum",
            stats.blocks_linked_with_competition,
            bounds.rules_linked_blocks_minimum,
            applied and enough_runs,
        ),
        _share_gate(
            "rules_link_round_dates",
            stats.linked_rounds_in_calendar,
            stats.linked_rounds,
            bounds.rules_link_round_dates,
            applied,
        ),
    )


def check_players(stats: PlayerStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The player reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        PLAYERS_READER,
        stats.records,
        evaluate_players(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "markerless_players": stats.markerless,
                "unresolved_teams": stats.with_team - stats.team_resolved,
            }
        ),
    )


def check_contracts(stats: ContractStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The contract reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        CONTRACTS_READER,
        stats.contracts,
        evaluate_contracts(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "past_dated_tail_ends": stats.tail_ends_past,
                "unparsed_tails": stats.chain_records - stats.tails_parsed,
                "tails_without_clause_table": stats.tails_without_clause_table,
                "date_marked_chain_records": stats.date_marked_chain_records,
                "players_without_contract_in_effect": stats.without_contract_in_effect,
            }
        ),
    )


def check_clubs(stats: ClubStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The club reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        CLUBS_READER,
        stats.records,
        evaluate_clubs(stats, bounds, game_db_bytes),
        FrozenMapping(
            {"unlinked_affiliate_teams": stats.affiliate_refs - stats.affiliate_refs_linked}
        ),
    )


def check_suspensions(
    stats: SuspensionStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The suspension reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        SUSPENSIONS_READER,
        stats.entries,
        evaluate_suspensions(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "suspensions_after_clock": stats.competition_issued_after_clock,
                "nation_bans_dated_ahead": stats.nation_issued_after_clock,
            }
        ),
    )


def check_managed(stats: ManagedStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The managed-club reader's record count and anomaly counts.

    This reader has no checks. A manager between jobs legitimately has no club, so no count
    or share it produces can carry a bound that a save between jobs would not fail as well,
    and a check that can never fail is worse than none at all. What guards it sits in the
    reader instead: it raises when its two routes to the club disagree. A route that resolved
    nothing is reported here as an anomaly.
    """
    humans_without_club = 1 if stats.human_count >= 1 and stats.rows == 0 else 0
    return ReaderCheck(
        MANAGED_CLUBS_READER,
        stats.rows,
        (),
        FrozenMapping(
            {
                "humans_without_club": humans_without_club,
                "club_route_one_unresolved": 1 - stats.route_one_resolved,
                "club_route_two_unresolved": 1 - stats.route_two_resolved,
            }
        ),
    )


def check_stages(stats: StageStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The stage reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        STAGES_READER,
        stats.rows,
        evaluate_stages(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "walk_gaps": stats.gaps,
                "rejected_competition_ids": stats.competition_id_rejected,
            }
        ),
    )


def check_competitions(
    stats: CompetitionStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The competition reader's checks, record count and anomaly counts."""
    return ReaderCheck(
        COMPETITIONS_READER,
        stats.competitions,
        evaluate_competitions(stats, bounds, game_db_bytes),
        FrozenMapping({"database_id_conflicts": stats.database_id_conflicts}),
    )


def check_fixtures(
    stats: FixtureStats, result_stats: ResultStats, bounds: GateBounds, span_bytes: int
) -> ReaderCheck:
    """The fixture reader's checks, record count and anomaly counts.

    The scores are fields of a fixture rather than a table of their own, so the result checks
    are reported here beside the calendar's, and the two sets of counts are kept apart: the
    calendar's own gates never see a result count, and the result gates never see a fixture
    count.

    `stray_records` and `stray_clusters` count what the span held outside the calendar, which
    every save carries some of, and `strays_without_a_copy` those of them the calendar holds
    no copy of, which is the only part of the drop that loses anything. The rest count kept
    fixtures a join or a decode left incomplete. `neutral_venue_votes` counts the clubs and
    seasons whose usual ground was decided: none of them on a full-size span means the venue
    vote never ran at all. `unresolved_stadiums` counts the records storing a ground the
    stadium table does not hold, which every save carries a few dozen of.

    `cache_records_excluded` counts independently owned noncalendar cache records removed
    before clustering. They are excluded from the calendar population and stray counts.

    `unjoined_results` counts the score records that named no match in this calendar, which is
    most of what a save holds: several seasons of history whose fixtures are long gone.
    `ambiguous_results` counts those naming more than one fixture at once, which fill none of
    them. `score_disagreements` counts matches two records gave two different scores, which no
    save measured has held, and `scored_fixtures` the played matches that ended up carrying a
    score. The `summary_` counts report the separate owned-summary source and its rejected
    keys; they do not contribute to the stage-result gates.
    """
    cluster_records = stats.cluster_records
    return ReaderCheck(
        FIXTURES_READER,
        cluster_records,
        evaluate_fixtures(stats, bounds, span_bytes)
        + evaluate_results(result_stats, bounds, span_bytes),
        FrozenMapping(
            {
                "stray_records": stats.span_records - cluster_records,
                "cache_records_excluded": stats.cache_records_excluded,
                "stray_clusters": max(stats.clusters - 1, 0),
                "strays_without_a_copy": stats.strays_without_a_copy,
                "fixtures_without_a_stage": cluster_records - stats.with_stage,
                "unresolved_stages": stats.with_stage - stats.stage_resolved,
                "unresolved_teams": (
                    2 * cluster_records - stats.home_team_resolved - stats.away_team_resolved
                ),
                "stub_team_references": stats.stub_team_references,
                "undated_fixtures": stats.undated,
                "bad_kick_off_slots": stats.bad_kick_off_slots,
                "neutral_venue_votes": stats.neutral_venue_votes,
                "unresolved_stadiums": stats.with_stadium - stats.stadium_resolved,
                "unjoined_results": result_stats.unjoined,
                "ambiguous_results": result_stats.ambiguous,
                "score_disagreements": result_stats.score_disagreements,
                "scored_fixtures": result_stats.scored_fixtures,
                "summary_lists_found": result_stats.summary_lists_found,
                "summary_lists_decoded": result_stats.summary_lists_decoded,
                "summary_records": result_stats.summary_records,
                "summary_invalid_scores": result_stats.summary_invalid_scores,
                "summary_unjoined": result_stats.summary_unjoined,
                "summary_ambiguous": result_stats.summary_ambiguous,
                "summary_for_unplayed": result_stats.summary_for_unplayed,
                "summary_unsafe_keys": result_stats.summary_unsafe_keys,
                "summary_existing_disagreements": result_stats.summary_existing_disagreements,
                "summary_stage_conflicts": result_stats.summary_stage_conflicts,
                "summary_scored_fixtures": result_stats.summary_scored_fixtures,
                "packet_score_records": result_stats.packet_score_records,
                "packet_unsafe_scores": result_stats.packet_unsafe_scores,
                "packet_for_unplayed": result_stats.packet_for_unplayed,
                "packet_stage_conflicts": result_stats.packet_stage_conflicts,
                "packet_summary_conflicts": result_stats.packet_summary_conflicts,
                "packet_existing_disagreements": result_stats.packet_existing_disagreements,
                "packet_scored_fixtures": result_stats.packet_scored_fixtures,
            }
        ),
    )


def check_transfer_windows(
    stats: TransferWindowStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The transfer-window reader's checks, record count and anomaly counts.

    The anomaly is the candidates the walk looked at and rejected for carrying no closing
    time, which is most of them: the date tags a window uses are shared by many records of the
    tagged stream, and only the closing time marks one as a window.
    """
    return ReaderCheck(
        TRANSFER_WINDOWS_READER,
        stats.windows,
        evaluate_transfer_windows(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "dated_records_without_a_closing_time": (
                    stats.markers - stats.windows - stats.incomplete
                ),
                "windows_with_unreadable_dates": stats.incomplete,
            }
        ),
    )


def check_league_tables(
    stats: LeagueTableStats, bounds: GateBounds, span_bytes: int
) -> ReaderCheck:
    """The league-table reader's checks, record count and anomaly counts.

    `duplicate_blocks` counts the repeated copies the span holds of a block already kept, which
    is about 45% of everything the span pass finds and is the reader's largest single
    correction. `rejected_block_candidates` counts the candidates the span pass judged and
    turned down. The rest count what the grouping and the joins left incomplete:
    `unresolved_groups` groups the calendar vote could not name, `blocks_outside_resolved_groups`
    the rows those groups hold, and the two team counts the rows whose team id is out of range
    or belongs to no club the save lists.

    The last two are the population the venue check judged rather than an anomaly in the usual
    sense, and they are reported because that check is the one here that an empty population
    leaves unjudged: `in_sync_tables` counts the tables whose rows account for exactly one
    season of the calendar, and `venue_slots_decided` the slots of those tables whose venue the
    calendar settles by itself. Both read zero on a layout that settles no slot parity.
    `started_calendar_divisions` is the population that decides whether the division floor
    applies: the divisions the calendar shows under way.
    """
    return ReaderCheck(
        LEAGUE_TABLES_READER,
        stats.groups,
        evaluate_league_tables(stats, bounds, span_bytes),
        FrozenMapping(
            {
                "duplicate_blocks": stats.duplicate_blocks,
                "rejected_block_candidates": (
                    stats.block_candidates - stats.blocks - stats.duplicate_blocks
                ),
                "unresolved_groups": stats.groups - stats.groups_resolved,
                "blocks_outside_resolved_groups": stats.blocks - stats.blocks_in_resolved_groups,
                "team_ids_out_of_range": stats.blocks - stats.team_id_in_range,
                "unresolved_teams": stats.blocks - stats.team_resolved,
                "in_sync_tables": stats.in_sync_tables,
                "venue_slots_decided": stats.venue_slots_decided,
                "started_calendar_divisions": stats.started_calendar_divisions,
            }
        ),
    )


def check_competition_rules(stats: RulesStats, bounds: GateBounds, span_bytes: int) -> ReaderCheck:
    """The competition-rules reader's checks, record count and anomaly counts.

    The first two anomalies count the two ways a block falls short of a full decode, which are
    reported rather than dropped: a block whose quad was not doubled still ships its lists and
    its calendar with the four quad fields empty, and a block whose lists or rounds did not
    decode still ships whatever did.

    The rest count the three ways the positional competition link comes back empty, which is
    the usual outcome rather than a fault: `blocks_without_a_run` counts the blocks the span
    stores no table block after, `blocks_with_an_ambiguous_run` those whose run is not exactly
    one table's set of clubs, and `linked_blocks_without_a_competition` those whose table the
    calendar vote could not name. Together they are the 32% to 45% of rows that carry no
    competition on the saves measured. `linked_round_shape` counts the linked blocks holding
    as many rounds as a table of that many clubs playing each other once or twice would; it is
    reported here because it does not separate from its own misalignment well enough to be a
    gate.
    """
    return ReaderCheck(
        COMPETITION_RULES_READER,
        stats.rows,
        evaluate_competition_rules(stats, bounds, span_bytes),
        FrozenMapping(
            {
                "blocks_not_fully_parsed": stats.blocks - stats.fully_parsed,
                "blocks_without_a_doubled_quad": stats.blocks - stats.quad_doubled,
                "blocks_without_a_run": stats.blocks - stats.blocks_with_run,
                "blocks_with_an_ambiguous_run": stats.blocks_with_run - stats.blocks_linked,
                "linked_blocks_without_a_competition": (
                    stats.blocks_linked - stats.blocks_linked_with_competition
                ),
                "linked_round_shape": stats.linked_round_shape,
            }
        ),
    )


def evaluate_season_stats(
    stats: SeasonStatsStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The season-statistics reader's checks, in a fixed order.

    The walk itself already failed on any record that does not read as one, so these judge
    what a structurally sound walk can still get wrong: records keyed by something other than a
    player, players the section has no record for, overall lines that are not the competitions
    added up, and minutes no appearances could hold. All four apply on a full-size save only.
    """
    applied = _applies(bounds, game_db_bytes)
    return (
        _share_gate(
            "season_stats_records_keyed_to_players",
            stats.records_keyed_to_players,
            stats.records,
            bounds.season_stats_records_keyed_to_players,
            applied,
        ),
        _share_gate(
            "season_stats_players_with_record",
            stats.players_with_record,
            stats.players,
            bounds.season_stats_players_with_record,
            applied,
        ),
        _share_gate(
            "season_stats_overall_sums_competitions",
            stats.overall_sums_competitions,
            stats.records_with_overall,
            bounds.season_stats_overall_sums_competitions,
            applied,
        ),
        _share_gate(
            "season_stats_minutes_in_range",
            stats.minutes_in_range,
            stats.lines,
            bounds.season_stats_minutes_in_range,
            applied,
        ),
    )


def check_season_history(stats: SeasonHistoryStats) -> ReaderCheck:
    """Report structural ownership counts without imposing current-season density gates."""
    return ReaderCheck(
        SEASON_HISTORY_READER,
        stats.rows,
        (),
        FrozenMapping(
            {
                "unowned_archive_units": stats.unowned_units,
                "unowned_history_lists": stats.unowned_lists,
                "players_without_history": stats.players_without_history,
                "unresolved_teams": stats.unresolved_teams,
            }
        ),
    )


def check_season_stats(
    stats: SeasonStatsStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The season-statistics reader's checks, row count and anomaly counts.

    `records_without_a_player` counts records whose key is no player's, which build no row,
    `records_repeating_a_key` records whose key an earlier record had, which build none either,
    and `unresolved_teams` the rows whose team no club lists, which keep their team id and leave
    the club fields empty.
    """
    return ReaderCheck(
        SEASON_STATS_READER,
        stats.rows,
        evaluate_season_stats(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "records_without_a_player": stats.records - stats.records_keyed_to_players,
                "records_repeating_a_key": stats.repeated_keys,
                "unresolved_teams": stats.rows - stats.teams_resolved,
            }
        ),
    )


def evaluate_player_match_stats(
    stats: MatchStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """Check match identities, statistics and complete declared list walks.

    No population floor is imposed because historical output varies with the career.
    Every recognized nonempty list must decode completely, independently of output year
    and ID bounds. An empty search fails unless every accepted player has an independently
    located null or explicitly empty history declaration. In that case there are no match
    identities or nonempty lists to judge, so their ratios remain None and do not apply.
    """
    applied = _applies(bounds, game_db_bytes)
    with_stats = stats.with_stats
    confirmed_empty = (
        stats.records == 0
        and stats.lists_found == 0
        and stats.lists_decoded == 0
        and stats.history_slots is not None
        and stats.history_slots > 0
        and stats.history_unknown == 0
        and stats.history_nonempty == 0
        and stats.history_containing_null is not None
        and stats.history_containing_null >= 0
        and stats.history_null is not None
        and stats.history_null >= 0
        and stats.history_empty is not None
        and stats.history_empty >= 0
        and stats.history_containing_null + stats.history_null + stats.history_empty
        == stats.history_slots
    )
    return (
        _gate(
            "per_match_competition_in_stage_space",
            _rate(stats.competition_in_stage_space, stats.records),
            bounds.per_match_competition_in_stage_space,
            applied and not confirmed_empty,
        ),
        _share_gate(
            "per_match_minutes_in_range",
            stats.minutes_in_range,
            with_stats,
            bounds.per_match_minutes_in_range,
            applied,
        ),
        _share_gate(
            "per_match_rating_in_range",
            stats.rating_in_range,
            with_stats,
            bounds.per_match_rating_in_range,
            applied,
        ),
        _gate(
            "per_match_lists_complete",
            _rate(stats.lists_decoded or 0, stats.lists_found or 0),
            bounds.per_match_lists_complete,
            applied and stats.lists_found is not None and not confirmed_empty,
        ),
    )


def check_player_match_stats(
    stats: MatchStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The per-match player stats reader's checks, record count and anomaly counts.

    `records_without_statistics` counts matches without stored statistics; fresh careers can
    have only these records, and they are ordinary rather than a fault. The rest count what a
    join or a bound left unsatisfied: opponents no club lists, competition ids
    the stage table does not name, statistics holding a number no match can reach, and records
    lying before the first player's window, which belong to no player and build no row.
    """
    records = stats.records
    history_counts = {
        name: value
        for name, value in (
            ("history_slots", stats.history_slots),
            ("history_containing_null", stats.history_containing_null),
            ("history_null", stats.history_null),
            ("history_empty", stats.history_empty),
            ("history_nonempty", stats.history_nonempty),
            ("history_unknown", stats.history_unknown),
        )
        if value is not None
    }
    return ReaderCheck(
        PLAYER_MATCH_STATS_READER,
        records,
        evaluate_player_match_stats(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "records_without_statistics": records - stats.with_stats,
                "unresolved_opponents": records - stats.opponent_resolved,
                "competitions_outside_the_stage_table": (
                    records - stats.competition_in_stage_space
                ),
                "statistics_outside_their_ranges": stats.with_stats - stats.stats_in_range,
                "records_without_an_owner": stats.unowned,
                "incomplete_match_lists": (stats.lists_found or 0) - (stats.lists_decoded or 0),
                **history_counts,
            }
        ),
    )


def evaluate_stadium_table(
    stats: StadiumStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The checks on the stadium table alone, in a fixed order.

    These are what the shared stadium index is handed out on, so they judge only what the
    table itself says: the rows walked, the pitch distribution, the owners and the capacities.
    The home-ground check needs the fixture calendar and joins the stadium reader's own checks
    instead.

    `stadium_rows_minimum` is what fails when the walk finds nothing, so the three shares
    beside it are free to report an empty population as not applied.
    """
    applied = _applies(bounds, game_db_bytes)
    rows = stats.rows
    return (
        _gate("stadium_rows_minimum", rows, bounds.stadium_rows_minimum, applied),
        _share_gate(
            "stadium_pitch_within_limits",
            stats.pitch_within_limits,
            stats.pitch_checked,
            bounds.stadium_pitch_within_limits,
            applied,
        ),
        _share_gate(
            "stadium_owners_resolved",
            stats.owners_resolved,
            stats.owners_set,
            bounds.stadium_owners_resolved,
            applied,
        ),
        _share_gate(
            "stadium_capacity_within_all_seater",
            stats.capacity_within_all_seater,
            rows,
            bounds.stadium_capacity_within_all_seater,
            applied,
        ),
    )


def evaluate_stadiums(
    stats: StadiumStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The stadium reader's checks, in a fixed order: the table's four and the home grounds.

    `stadium_home_grounds_owned` is the one that says the ordinal a fixture stores still names
    the row it did: shifting it by one either way leaves almost no club playing at a ground it
    owns. It applies only when some club both owns a ground and has a calendar home ground,
    because a career whose calendar is too young to give any club four home matches has an
    empty population rather than a broken join.
    """
    return (
        *evaluate_stadium_table(stats, bounds, game_db_bytes),
        _share_gate(
            "stadium_home_grounds_owned",
            stats.owning_clubs_home_ground_owned,
            stats.owning_clubs_with_home_ground,
            bounds.stadium_home_grounds_owned,
            _applies(bounds, game_db_bytes),
        ),
    )


def check_stadiums(stats: StadiumStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The stadium reader's checks, record count and anomaly counts.

    `walk_stopped_before_the_table_end` is 1 when the walk stopped inside the table instead of
    on the word that follows its last row. That is the one anomaly here a share cannot show:
    every ground past the stopping point is missing from the rows **and** from the denominator
    of each share, so a walk that read half the table can still score a perfect rate on what it
    did read.

    `named_rows` counts the grounds that carry a name at all, which is a couple of hundred out
    of tens of thousands: every other name comes from the game's installed database.
    `unresolved_owners` counts grounds naming
    a club the save does not list, and `unset_capacities` the grounds whose capacity field is
    zero, which is about four in five. `clubs_with_home_ground` counts the clubs the calendar
    gave a home ground: none of them on a full-size save means the vote never ran.
    """
    return ReaderCheck(
        STADIUMS_READER,
        stats.rows,
        evaluate_stadiums(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "walk_stopped_before_the_table_end": 1 - stats.table_end_reached,
                "named_rows": stats.named_rows,
                "unresolved_owners": stats.owners_set - stats.owners_resolved,
                "unset_capacities": stats.rows - stats.capacity_set,
                "clubs_with_home_ground": stats.clubs_with_home_ground,
            }
        ),
    )


def evaluate_injury_types(
    stats: InjuryTypeStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The injury-type reader's one check.

    It applies on a full-size save that lists at least one per-match entry. A save that lists
    none holds these names nowhere at all, so its empty table is a fact about the save rather
    than a layout that has moved, and the check is reported as not applied instead of failing.
    """
    applied = _applies(bounds, game_db_bytes) and stats.match_entries >= 1
    return (
        _gate(
            "injury_type_entries_minimum",
            stats.table_entries,
            bounds.injury_type_entries_minimum,
            applied,
        ),
    )


def check_injury_types(
    stats: InjuryTypeStats, bounds: GateBounds, game_db_bytes: int
) -> ReaderCheck:
    """The injury-type reader's check, record count and anomaly counts.

    The anomalies say how much of the save was reached: how many per-match entries it lists at
    all, how many of those read are not per-match files, and how many were read looking for the
    table. A save listing none reports zero entries, which is how an empty table is told from a
    table that failed to decode.
    """
    return ReaderCheck(
        INJURY_TYPES_READER,
        stats.table_entries,
        evaluate_injury_types(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "match_entries": stats.match_entries,
                "entries_without_magic": stats.entries_without_magic,
                "entries_tried": stats.entries_with_magic_tried,
            }
        ),
    )


def evaluate_injuries(stats: InjuryStats, bounds: GateBounds) -> tuple[GateResult, ...]:
    """The injuries reader's checks, in a fixed order.

    They judge a section of a few megabytes rather than `game_db`, so they apply from that
    section's own size: a smaller one comes from a fragment that cannot meet full-save counts.

    The walk is the structural check and it raises rather than scoring here, because the
    section is four arrays and three lists back to back with no signature to search for: a
    start or a stride read wrong cannot consume it exactly. What these shares add is a
    judgement of each row's own shape and of the two joins the rows carry, and every one of
    them separates a sound decode from the same rows read one or four bytes late.

    `injury_log_ascending` is judged on the steps between rows whose date decodes, and it is
    deliberately **not** excused when there are no such steps: a section full of rows from
    which not one date decodes is what a decode read one byte out looks like, so it fails
    there for want of a rate. The typed shares are excused when
    the section holds no typed row, and the recent-team share when no row of the last month
    has a player with a team, because a career can legitimately hold neither. The type share
    is excused as well when the name table is empty, since a save carrying no per-match file
    holds these names nowhere at all.

    `injury_typed_dates_near_clock` is a share of **every** typed row, not of the dated ones.
    Taken over the dated rows it is 1.0 read correctly and 1.0 read one byte late as well, so
    it could not fail its own misalignment; over every typed row it falls from 0.988 to zero.
    It subsumes a plain check on how many rows carry a date and catches one thing more: a date
    read from neighbouring bytes that decodes to a year the game has long passed, which is
    where every date that still decodes one byte late lands. The band it judges against is
    much wider than any deviation measured, because how far behind the in-game date the game
    keeps a typed row is career state: five of the seven save states measured held nothing
    older than seven days and two held a full day's rows at eight days, so a bound drawn
    tight round either figure fails a section read correctly. `typed_rows_over_a_week_old` is
    reported as an anomaly for that reason and no gate judges it.

    One counted share carries no gate: how many log rows still name a player runs 0.94 to
    0.96 and is career state, since a person the save no longer keeps as a player is a real
    row the game still shows. It is reported as an anomaly instead.
    """
    applied = stats.section_bytes >= bounds.injury_manager_minimum_applies_from_bytes
    log_rows = stats.log_rows
    typed_rows = stats.typed_rows
    typed_applied = applied and typed_rows > 0
    return (
        _gate(
            "injury_log_lead_byte",
            _rate(stats.log_lead_ok, log_rows),
            bounds.injury_log_lead_byte,
            applied,
        ),
        _gate(
            "injury_log_dates",
            _rate(stats.log_dates_ok, log_rows),
            bounds.injury_log_dates,
            applied,
        ),
        _gate(
            "injury_log_ascending",
            _rate(stats.log_ascending_steps, stats.log_steps),
            bounds.injury_log_ascending,
            applied,
        ),
        _gate(
            "injury_log_teams_resolved",
            _rate(stats.log_teams_resolved, log_rows),
            bounds.injury_log_teams_resolved,
            applied,
        ),
        _share_gate(
            "injury_log_recent_team_matches",
            stats.recent_log_team_matches,
            stats.recent_log_rows,
            bounds.injury_log_recent_team_matches,
            applied,
        ),
        _gate(
            "injury_typed_lead_byte",
            _rate(stats.typed_lead_ok, typed_rows),
            bounds.injury_typed_lead_byte,
            typed_applied,
        ),
        _gate(
            "injury_typed_dates_near_clock",
            _rate(stats.typed_dated_near_clock, typed_rows),
            bounds.injury_typed_dates_near_clock,
            typed_applied,
        ),
        _gate(
            "injury_typed_types_resolved",
            _rate(stats.typed_types_resolved, typed_rows),
            bounds.injury_typed_types_resolved,
            typed_applied and stats.type_table_entries > 0,
        ),
    )


def check_injuries(stats: InjuryStats, bounds: GateBounds) -> ReaderCheck:
    """The injuries reader's checks, record count and anomaly counts.

    The window row counts and the three list entry counts are the five parts of the section no
    row comes from: they are reported so that a walk which consumed the section exactly still
    says what it passed over. `log_rows_without_a_player` and `typed_rows_without_a_player`
    count the rows whose person the save no longer keeps as a player, which no gate judges.
    `unresolved_log_teams`, `untyped_rows`, `undated_typed_rows` and
    `typed_rows_far_from_the_clock` split what the gated shares left out: the last two
    together are what `injury_typed_dates_near_clock` counts against, and every save measured
    holds the first of them and none of the second. `typed_rows_over_a_week_old` counts the
    dated typed rows further behind the in-game date than a week, which runs from none to a
    tenth of the rows depending on the save state and is career state rather than layout.
    """
    first_list, second_list, third_list = (stats.list_entries + (0, 0, 0))[:3]
    return ReaderCheck(
        INJURIES_READER,
        stats.log_rows + stats.typed_rows,
        evaluate_injuries(stats, bounds),
        FrozenMapping(
            {
                "window_a_rows": stats.window_a_rows,
                "window_b_rows": stats.window_b_rows,
                "list_0_entries": first_list,
                "list_1_entries": second_list,
                "list_2_entries": third_list,
                "log_rows_without_a_player": stats.log_rows - stats.log_players_resolved,
                "typed_rows_without_a_player": stats.typed_rows - stats.typed_players_resolved,
                "unresolved_log_teams": stats.log_rows - stats.log_teams_resolved,
                "untyped_rows": stats.typed_rows - stats.typed_types_resolved,
                "undated_typed_rows": stats.typed_rows - stats.typed_dated,
                "typed_rows_far_from_the_clock": stats.typed_dated - stats.typed_dated_near_clock,
                "typed_rows_over_a_week_old": stats.typed_dated_over_a_week_old,
            }
        ),
    )


def evaluate_finances(
    stats: FinanceStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The finance reader's checks, in a fixed order.

    The three shares judge the rows that were decoded, so each applies only where it has a
    denominator: a save whose clubs keep no series at all is a save with nothing to judge, not a
    broken decode. Only the clubs of the one or two league nations a save tracks keep a series,
    and which nations those are changes during a career, so an empty result has to be allowed.

    The series floor is what catches a locator that has stopped finding chains, and it applies
    only where the save lists a managed club, whose own club held a series on every save
    measured. That leaves one hole, deliberately: on a save with no human manager a locator
    finding nothing returns an empty table and raises nothing. No count of club records could
    close it without failing a save that legitimately tracks no league nation the manager is in,
    and `clubs_with_series` and `records_searched` are reported as anomalies either way.
    """
    applied = _applies(bounds, game_db_bytes)
    rows = stats.rows
    return (
        _gate(
            "finance_net_identity",
            _rate(stats.net_identity_rows, rows),
            bounds.finance_net_identity,
            applied and rows > 0,
        ),
        _gate(
            "finance_balance_continuity",
            _rate(stats.balance_continuous_steps, stats.balance_steps),
            bounds.finance_balance_continuity,
            applied and stats.balance_steps > 0,
        ),
        _gate(
            "finance_expenditure_split",
            _rate(stats.expenditure_split_rows, rows),
            bounds.finance_expenditure_split,
            applied and rows > 0,
        ),
        _gate(
            "finance_clubs_with_two_chains",
            stats.clubs_with_two_chains,
            bounds.finance_clubs_with_two_chains,
            applied,
        ),
        _gate(
            "finance_series_minimum",
            stats.clubs_with_series,
            bounds.finance_series_minimum,
            applied and stats.managed_club_exists,
        ),
    )


def evaluate_sponsorships(
    stats: FinanceStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """Judge coverage of the structurally located primary sponsor lists.

    A nonempty list with valid rows and an explicitly counted empty list both establish
    coverage. Missing prefixes and invalid positive lists remain uncovered. The existing
    share and count bounds apply to that coverage, including when every list is empty.
    """
    applied = _applies(bounds, game_db_bytes)
    decoded_lists = stats.clubs_with_sponsors + stats.clubs_with_empty_sponsor_lists
    return (
        _gate(
            "finance_clubs_with_sponsors",
            _rate(decoded_lists, stats.clubs_with_series),
            bounds.finance_clubs_with_sponsors,
            applied and stats.clubs_with_series > 0,
        ),
        _gate(
            "sponsor_clubs_minimum",
            decoded_lists,
            bounds.sponsor_clubs_minimum,
            applied and stats.managed_club_exists,
        ),
    )


def evaluate_facilities(
    stats: FacilityStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The facilities reader's checks, in a fixed order.

    The share judges the clubs that keep a finance series, which are the only clubs that carry
    a rating, so it applies only where there is one of those: a save whose clubs keep no series
    has no rating to read, exactly as it has no month to read. It is what catches a rating read
    from the wrong offset, since the bytes around it hold a value inside the range on a few
    clubs in a hundred rather than on all of them. A club whose rating is unset stores no
    rating at all, so it is left out of that share rather than counted against it, and the
    unset share has a ceiling of its own: a read landing in a zeroed stretch for most clubs
    would otherwise leave the in-range share almost nothing to judge.

    The count floor is the finance floor's, for the same population: at least one club with a
    series, applied only where the save lists a managed club, whose own club held a series on
    every save measured. A save with no human manager whose clubs keep no series is the one
    hole, the same one `finances()` documents, and `fmsave validate` reports the counts.
    """
    applied = _applies(bounds, game_db_bytes)
    return (
        _share_gate(
            "facility_byte_in_range",
            stats.in_range,
            stats.clubs_with_series - stats.unset,
            bounds.facility_byte_in_range,
            applied,
        ),
        _share_gate(
            "facility_unset_ratings",
            stats.unset,
            stats.clubs_with_series,
            bounds.facility_unset_ratings,
            applied,
        ),
        _gate(
            "facility_clubs_minimum",
            stats.clubs_with_series,
            bounds.facility_clubs_minimum,
            applied and stats.managed_club_exists,
        ),
    )


def evaluate_affiliates(
    stats: AffiliateStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The affiliate-group reader's one check.

    It applies on a full-size save whose section stores at least one group member. A section
    storing no group has no member to resolve, and an empty population is a fact about the save
    rather than a layout that has moved, so the check is reported as not applied instead of
    failing for want of a rate. What the walk itself cannot do is end quietly on the wrong
    bytes: it has to consume exactly the groups the header claims and stop on the section's last
    byte, and it raises when it does not.

    What this check judges is the index space rather than the walk. The stored values are club
    indexes exactly as they are, and reading them one higher still resolves most of them,
    because the index is dense: the share falls only to about 0.86, which is below both the
    floor and the 0.91 a random index of this range would reach by chance.
    """
    applied = _applies(bounds, game_db_bytes) and stats.members > 0
    return (
        _gate(
            "affiliate_members_resolved",
            _rate(stats.members_resolved, stats.members),
            bounds.affiliate_members_resolved,
            applied,
        ),
    )


def check_affiliates(stats: AffiliateStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The affiliate-group reader's check, record count and anomaly counts.

    The anomaly counts the members whose stored club index no club record claims, which every
    save measured carries a handful of: those indexes fall in gaps of the index rather than
    naming another club.
    """
    return ReaderCheck(
        AFFILIATES_READER,
        stats.groups,
        evaluate_affiliates(stats, bounds, game_db_bytes),
        FrozenMapping({"unresolved_members": stats.members - stats.members_resolved}),
    )


def evaluate_job_vacancies(stats: JobVacancyStats, bounds: GateBounds) -> tuple[GateResult, ...]:
    """The job-vacancy reader's checks, in a fixed order.

    They judge a section of a few kilobytes rather than `game_db`, so they apply from a record
    count instead of a section size: a feed of fewer than
    `GateBounds.job_vacancy_minimum_applies_from_records` records, an empty one included, is a
    fact about a career rather than a layout that has moved. The feed is career state, it keeps
    vacancies years old, and a manager between jobs may see very little of it, so **no floor is
    put under its size at all** and no share is judged on a handful of rows.

    That leaves a hole a share cannot close: a locator reading the wrong section would return an
    empty table and apply nothing. What closes it is structural rather than statistical, and it
    sits in the reader: the section's size has to be its header plus its record size times the
    stored count, exactly, and nothing else about the feed can satisfy that. It is also the one
    test a start shifted by a whole record fails, since every share below then passes on the
    next record's bytes.

    `job_vacancy_advertised_ascending` is judged on the steps between records whose advertised
    date decodes, not on the records, and it is deliberately **not** excused when there are no
    such steps. A feed of twenty records or more from which not one date decodes is what a
    decode read one byte out looks like, so it fails there for want of a rate.

    Two counted shares carry no gate. Team ids resolve on 0.93 to 0.98 of records, but ids are
    about 92% dense over the range the feed uses, so no floor could separate a sound decode from
    a wrong one. Competition ids the stage table names are 1.0 of records read correctly and
    also 1.0 with the record start shifted four bytes on every save measured, so that share
    cannot fail either. Both are reported as counts instead.
    """
    records = stats.records
    applied = records >= bounds.job_vacancy_minimum_applies_from_records
    return (
        _gate("job_vacancy_tag", _rate(stats.tagged, records), bounds.job_vacancy_tag, applied),
        _gate(
            "job_vacancy_dates_ordered",
            _rate(stats.dates_ordered, records),
            bounds.job_vacancy_dates_ordered,
            applied,
        ),
        _gate(
            "job_vacancy_advertised_ascending",
            _rate(stats.advertised_ascending_steps, stats.advertised_steps),
            bounds.job_vacancy_advertised_ascending,
            applied,
        ),
        _gate(
            "job_vacancy_reserved_zero",
            _rate(stats.reserved_zero, records),
            bounds.job_vacancy_reserved_zero,
            applied,
        ),
    )


def check_finances(stats: FinanceStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The finance reader's checks, record count and anomaly counts.

    `clubs_with_series` is reported as an anomaly because it is career state rather than a
    fault: a save tracks one or two league nations, and only their clubs keep a series at all.
    `balance_breaks` counts the consecutive months whose balance step differs from the month's
    net, which every save holds some of, clustered in the transfer-window months.
    `opening_balance_steps` counts the first steps whose oldest row stores an opening balance,
    which the continuity check accepts; most clubs whose series begins with the career have one.
    """
    return ReaderCheck(
        FINANCES_READER,
        stats.rows,
        evaluate_finances(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "clubs_with_series": stats.clubs_with_series,
                "balance_breaks": stats.balance_steps - stats.balance_continuous_steps,
                "opening_balance_steps": stats.opening_balance_steps,
            }
        ),
    )


def check_job_vacancies(stats: JobVacancyStats, bounds: GateBounds) -> ReaderCheck:
    """The job-vacancy reader's checks, record count and anomaly counts.

    `unresolved_teams` counts the vacancies whose team id no club lists, a handful on every
    save. `competitions_outside_the_competition_table` counts those naming a competition the
    stage table does not, which carries no gate and is reported here instead.
    `without_competition` and `without_league_position` count the rows the save simply stores
    nothing in those fields for, about a quarter of them for the position, and `flagged` the
    rows whose unnamed 0/1 flag is set.
    """
    records = stats.records
    return ReaderCheck(
        JOB_VACANCIES_READER,
        records,
        evaluate_job_vacancies(stats, bounds),
        FrozenMapping(
            {
                "unresolved_teams": records - stats.teams_resolved,
                "competitions_outside_the_competition_table": records - stats.competitions_known,
                "without_competition": records - stats.with_competition,
                "without_league_position": records - stats.with_league_position,
                "flagged": stats.flagged,
            }
        ),
    )


def evaluate_staff(
    stats: StaffStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The staff reader's checks, in a fixed order.

    The four object shares judge the staff objects the rows were built from, so each applies
    only where one was read; the block share and the count floor apply on a full-size save,
    where the smallest population measured runs to thousands of people. The listing share judges
    the pairs the club lists give, so it applies only where a club lists somebody, which every
    full-size save measured has thousands of clubs doing.

    The unowned count is what catches a header test that has stopped recognising a person's own
    object: every contract record with a tail on every save measured has its person's header in
    front of it, and with the kind byte read one place out none of them does.
    """
    applied = _applies(bounds, game_db_bytes)
    staff_objects = stats.staff_objects
    return (
        _gate(
            "staff_ability_signature",
            _rate(stats.ability_signatures, staff_objects),
            bounds.staff_ability_signature,
            applied and staff_objects > 0,
        ),
        _gate(
            "staff_preference_slots",
            _rate(stats.preference_slots_in_range, staff_objects),
            bounds.staff_preference_slots,
            applied and staff_objects > 0,
        ),
        _gate(
            "staff_codes_in_set",
            _rate(stats.codes_in_set, staff_objects),
            bounds.staff_codes_in_set,
            applied and staff_objects > 0,
        ),
        _gate(
            "staff_block_40_in_range",
            _rate(stats.block_40_in_range, staff_objects),
            bounds.staff_block_40_in_range,
            applied and staff_objects > 0,
        ),
        _gate(
            "staff_person_blocks",
            _rate(stats.persons_with_block, stats.persons),
            bounds.staff_person_blocks,
            applied and stats.persons > 0,
        ),
        _gate("staff_minimum", stats.persons, bounds.staff_minimum, applied),
        _gate(
            "staff_listed_contracted_here",
            _rate(stats.listed_pairs_contracted_here, stats.listed_pairs),
            bounds.staff_listed_contracted_here,
            applied and stats.listed_pairs > 0,
        ),
        _gate(
            "staff_unowned_tailed_contracts",
            stats.unowned_tailed_hits,
            bounds.staff_unowned_tailed_contracts,
            applied,
        ),
    )


def evaluate_staff_lists(
    stats: StaffStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The club staff lists reader's two checks, in a fixed order.

    The first judges the club records that carry a team list, which is where the staff lists
    follow, and the second the people those lists name. Both apply only where they have a
    denominator: a fragment holding no club record with a team list, or no club that lists
    anybody, has nothing to judge rather than a layout that has moved.
    """
    applied = _applies(bounds, game_db_bytes)
    return (
        _gate(
            "staff_lists_fit",
            _rate(stats.clubs_lists_fit, stats.clubs_checked),
            bounds.staff_lists_fit,
            applied and stats.clubs_checked > 0,
        ),
        _gate(
            "staff_list_ids_are_staff",
            _rate(stats.listed_persons_staff, stats.listed_persons),
            bounds.staff_list_ids_are_staff,
            applied and stats.listed_persons > 0,
        ),
    )


def check_staff(stats: StaffStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The staff reader's checks, record count and anomaly counts.

    `club_record_hits` counts candidates inside closed club objects, which are not people.
    `untailed_hits` counts the remaining filtered hits that are not a contract record at all,
    which every save has tens of thousands of. `ambiguous_headers` and `unlocated_persons`
    count the people left without a row, a handful at most. `unresolved_contract_teams` counts
    the records naming a team no club lists, `repeat_contracts` the people holding two records
    at one club, and `merged_affiliate_pairs` the listings an affiliate side made that became a
    row at its parent. `human_manager_missing` is one where the save lists a human manager
    whose own object or contract could not be read, and zero otherwise.
    """
    return ReaderCheck(
        STAFF_READER,
        stats.rows,
        evaluate_staff(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "untailed_hits": stats.untailed_hits,
                "club_record_hits": stats.club_record_hits,
                "ambiguous_headers": stats.ambiguous_headers,
                "unlocated_persons": stats.unlocated_persons,
                "unresolved_contract_teams": stats.unresolved_contract_teams,
                "repeat_contracts": stats.repeat_contracts,
                "merged_affiliate_pairs": stats.merged_affiliate_pairs,
                "human_manager_missing": 0 if stats.human_found else 1,
                "non_staff_tailed_hits": stats.non_staff_tailed_hits,
            }
        ),
    )


def check_staff_lists(stats: StaffStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The club staff lists reader's checks, record count and anomaly count.

    The anomaly counts the list values that turn out to be player pindexes, which a handful of
    clubs on every save hold and which no list row keeps.
    """
    return ReaderCheck(
        STAFF_LISTS_READER,
        stats.list_rows,
        evaluate_staff_lists(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "player_values_in_lists": stats.player_values_in_lists,
                "unset_list_values": stats.unset_list_values,
            }
        ),
    )


def check_facilities(stats: FacilityStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The facilities reader's checks, record count and anomaly counts.

    `clubs_without_a_rating` counts the clubs with a finance series whose record ends before
    the rating would sit, which no save measured holds any of, `ratings_out_of_range` the
    ratings outside the range the layout carries that are not unset, which the in-range share
    bounds, and `unset_ratings` the clubs whose rating is unset, which the unset share bounds.
    """
    return ReaderCheck(
        FACILITIES_READER,
        stats.rows,
        evaluate_facilities(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "clubs_without_a_rating": stats.clubs_with_series - stats.rows,
                "ratings_out_of_range": stats.rows - stats.in_range - stats.unset,
                "unset_ratings": stats.unset,
            }
        ),
    )


def check_sponsorships(stats: FinanceStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """Primary sponsor-list coverage, row count and empty/missing diagnostics.

    The existing `clubs_without_sponsors` counts clubs returning no sponsor rows. The
    separate empty-list count identifies confirmed absence; `clubs_without_sponsor_lists`
    counts unresolved or invalid lists rather than treating those as empty.
    """
    return ReaderCheck(
        SPONSORSHIPS_READER,
        stats.sponsor_rows,
        evaluate_sponsorships(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "clubs_without_sponsors": stats.clubs_with_series - stats.clubs_with_sponsors,
                "clubs_with_empty_sponsor_lists": stats.clubs_with_empty_sponsor_lists,
                "clubs_without_sponsor_lists": stats.clubs_with_series
                - stats.clubs_with_sponsors
                - stats.clubs_with_empty_sponsor_lists,
            }
        ),
    )


def evaluate_tactics(
    stats: TacticStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The tactic reader's checks, in a fixed order.

    They apply on a full-size save that lists a managed club. A manager between jobs has no
    team block to read, so both tables are empty and nothing here is judged: that is a fact
    about the career rather than a layout that has moved.

    `tactics_team_blocks_match_club` carries the header's own claim as well as the blocks
    found, because the two fail differently: a team-id locator that has moved leaves a team
    without its single block, while a header read from the wrong offset claims a number of
    blocks that is not the number the section stores at all. The header counts every team the
    manager runs, national teams included, so it is compared with the blocks found by
    structure. Club teams can have no stored block, so coverage compares the team-id locator
    with the structurally located blocks naming club teams. Duplicate stored blocks count
    separately and cannot be excused as absent teams. A disagreeing header or an inventory
    with no club blocks scores zero whatever the locator found.

    The record-count share checks the team's declared count independently.
    The two walk shares are judged on all stored tactic records. They are excused when the
    team blocks claim no tactics; a new career can have none saved yet. If any block claims
    records but none decode, both shares and the independent record-count check fail.
    The two selector shares are excused without a denominator, because a block legitimately
    stores no selection at all, and the second is judged on the selectors that resolved.
    """
    applied = _applies(bounds, game_db_bytes) and stats.managed_club_exists
    slots_applied = applied and (stats.tactic_blocks > 0 or stats.stored_tactics > 0)
    header_agrees = (
        stats.header_blocks == stats.stored_blocks
        and 0 < stats.stored_club_blocks <= min(stats.club_team_count, stats.stored_blocks)
    )
    blocks_found = stats.blocks_found if header_agrees else 0
    return (
        _gate(
            "tactics_manager_selector_matches",
            int(stats.selector_matches),
            bounds.tactics_manager_selector_matches,
            applied,
        ),
        _gate(
            "tactics_team_blocks_match_club",
            _rate(blocks_found, stats.stored_club_blocks) if header_agrees else 0.0,
            bounds.tactics_team_blocks_match_club,
            applied,
        ),
        _share_gate(
            "tactic_records_count_matching",
            stats.tactic_blocks_count_matching,
            stats.tactic_blocks,
            bounds.tactic_records_count_matching,
            applied,
        ),
        _gate(
            "tactic_slot_walks_complete",
            _rate(stats.slot_walks_complete, stats.stored_tactics),
            bounds.tactic_slot_walks_complete,
            slots_applied,
        ),
        _gate(
            "tactic_oop_index_permutations",
            _rate(stats.oop_index_permutations, stats.stored_tactics),
            bounds.tactic_oop_index_permutations,
            slots_applied,
        ),
        _share_gate(
            "tactic_selection_selectors_resolved",
            stats.selection_selectors_resolved,
            stats.selection_selectors,
            bounds.tactic_selection_selectors_resolved,
            applied,
        ),
        _share_gate(
            "tactic_selection_selectors_at_club",
            stats.selection_selectors_at_club,
            stats.selection_selectors_resolved,
            bounds.tactic_selection_selectors_at_club,
            applied,
        ),
    )


def evaluate_set_pieces(
    stats: TacticStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The set-piece reader's one check: every block holds its full set of routine slots.

    It is the check that says the routine locator still ends where a routine ends. Decoding a
    name from beside the terminator instead of in front of it leaves no block with a full set
    of slots on any save measured, and it applies wherever a block was read at all.
    """
    return (
        _share_gate(
            "set_piece_blocks_complete",
            stats.routine_blocks_complete,
            stats.routine_blocks,
            bounds.set_piece_blocks_complete,
            _applies(bounds, game_db_bytes) and stats.managed_club_exists,
        ),
    )


def check_tactics(stats: TacticStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The tactic reader's checks, record count and anomaly counts.

    `preset_tactics` counts records carrying the preset signature within a team's declared
    list. They are decoded along with its other stored tactics.
    `tactic_blocks_count_mismatched` counts the blocks that claim more tactic records than the
    walk found signatures for, and `unresolved_selectors` the selectors no player record names.
    """
    return ReaderCheck(
        TACTICS_READER,
        stats.stored_tactics,
        evaluate_tactics(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "preset_tactics": stats.preset_tactics,
                "non_club_blocks": stats.stored_blocks - stats.stored_club_blocks,
                "tactic_blocks_count_mismatched": (
                    stats.tactic_blocks - stats.tactic_blocks_count_matching
                ),
                "unresolved_selectors": (
                    stats.selection_selectors - stats.selection_selectors_resolved
                ),
            }
        ),
    )


def check_set_pieces(stats: TacticStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The set-piece reader's check, record count and anomaly count.

    `named_routines` is reported rather than gated: a first team carries ten named routines on
    every save measured and every other team carries none, so the count is career state.
    """
    return ReaderCheck(
        SET_PIECES_READER,
        stats.routines,
        evaluate_set_pieces(stats, bounds, game_db_bytes),
        FrozenMapping({"named_routines": stats.named_routines}),
    )


def evaluate_training(
    stats: TrainingStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The training reader's checks, in a fixed order.

    Both apply on a full-size save where the manager runs a club, and only there: the section
    holds one calendar per team of that club and nothing for any other club, so a save with no
    managed club has nothing here to judge rather than a decode that went wrong.

    The first says the walk found the whole team list, which it did on every save measured;
    started one byte or four bytes late it finds no block at all, and its denominator is the
    club's own team count, which is zero only when something is already broken. So it is the
    one that fails when the walk has moved, and it applies whatever the walk found.

    The second says consecutive weeks step a week, which held on every pair of every calendar
    measured. It judges the steps that were read, so it is not applied when there are none: a
    club whose every team held one weekly record or fewer would otherwise fail a check on a
    healthy save, and the shifted walk that leaves no step to judge is already caught beside
    it, on the same fault.
    """
    applied = _applies(bounds, game_db_bytes) and stats.managed_club_exists
    return (
        _gate(
            "training_blocks_match_club_teams",
            _rate(stats.blocks, stats.club_team_count),
            bounds.training_blocks_match_club_teams,
            applied,
        ),
        _share_gate(
            "training_week_steps",
            stats.seven_day_steps,
            stats.week_steps,
            bounds.training_week_steps,
            applied,
        ),
    )


def evaluate_mentoring(
    stats: TrainingStats, bounds: GateBounds, game_db_bytes: int
) -> tuple[GateResult, ...]:
    """The mentoring reader's one check.

    It applies on a full-size save where the manager runs a club **and** a group member
    resolved to a player, because a manager who mentors nobody is ordinary: every save measured
    has teams with no group at all, and one has a whole team of the club with none.

    What it judges is the index space the stored selectors live in. Each is a player's record
    index plus one, and reading one of them a place out still finds a player, because the
    index is dense over the range a squad occupies: on the saves measured that read resolves
    most or all members, which no floor can tell from the 1.0 a correct
    read scores. So **there is no check on how many members resolve**; what the wrong read
    cannot do is land on players of the right club, and this share falls from 1.0 to at most
    0.18 when it happens. A shifted walk cannot reach here at all: the groups sit inside a
    block, so the training checks fail first.
    """
    applied = _applies(bounds, game_db_bytes) and stats.managed_club_exists
    return (
        _share_gate(
            "mentoring_members_at_club",
            stats.members_at_club,
            stats.members_resolved,
            bounds.mentoring_members_at_club,
            applied,
        ),
    )


def check_training(stats: TrainingStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The training reader's checks, record count and anomaly counts.

    The anomalies are counts rather than faults: the weeks whose stored date does not decode,
    the per-person header entries the reader does not decode at all, and the saved schedules
    found after the last block, which a manager who has saved none legitimately has none of.
    """
    return ReaderCheck(
        TRAINING_READER,
        stats.blocks,
        evaluate_training(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "undated_weeks": stats.undated_weeks,
                "header_entries": stats.header_entries,
                "library_entries": stats.library_entries,
            }
        ),
    )


def check_mentoring(stats: TrainingStats, bounds: GateBounds, game_db_bytes: int) -> ReaderCheck:
    """The mentoring reader's check, record count and anomaly counts.

    `members_without_a_player` counts the members whose stored selector names no player record,
    and `members_elsewhere` the resolved members who are not players of the managed club. The
    first carries no gate, because a selector read a place out still resolves; see
    `evaluate_mentoring`.
    """
    return ReaderCheck(
        MENTORING_READER,
        stats.groups,
        evaluate_mentoring(stats, bounds, game_db_bytes),
        FrozenMapping(
            {
                "members_without_a_player": stats.members - stats.members_resolved,
                "members_elsewhere": stats.members_resolved - stats.members_at_club,
            }
        ),
    )


def _format_number(value: float | None) -> str:
    if value is None:
        return "none"
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return repr(rounded)


def _format_bound(value: float | None) -> str:
    return "" if value is None else _format_number(value)


def _likely_cause(gate_name: str) -> str:
    """ "; likely <cause>" for a check whose failure has one likely cause, else ""."""
    cause = _LIKELY_CAUSES.get(gate_name)
    return "" if cause is None else f"; likely {cause}"


def _failure_summary(reader_name: str, results: Sequence[GateResult]) -> str | None:
    """ "<reader> failed checks: <gate>=<observed> (expected <min>..<max>); ...", or None."""
    failures = [
        f"{result.name}={_format_number(result.observed)} "
        f"(expected {_format_bound(result.minimum)}..{_format_bound(result.maximum)}"
        f"{_likely_cause(result.name)})"
        for result in results
        if result.applied and not result.passed
    ]
    if not failures:
        return None
    return f"{reader_name} failed checks: {'; '.join(failures)}"


# A warning is issued against the first frame outside this package, so a reader's caller sees
# its own line rather than a line of fmsave's, however many frames deep the reader sits.
_PACKAGE_FILE_PREFIX = os.path.dirname(__file__)


def _warn_failure(message: str) -> None:
    warnings.warn(
        message,
        ReaderCheckWarning,
        stacklevel=2,
        skip_file_prefixes=(_PACKAGE_FILE_PREFIX,),
    )


def enforce(reader_name: str, results: Sequence[GateResult], *, strict: bool) -> bool:
    """Report a failed applied check. The message holds only rounded rates and bounds.

    On a strict save the failure is raised, and on any other save it is warned about with that
    same message and the reader hands its table back: a bound measured on a handful of saves
    is not something to refuse a whole save over.

    Returns:
        Whether a failure was warned about, which is False on a strict save and whenever
        every applied check passed.

    Raises:
        ReaderCheckError: An applied check failed and `strict` is True.

    Warns:
        ReaderCheckWarning: An applied check failed and `strict` is False.
    """
    summary = _failure_summary(reader_name, results)
    if summary is None or not _gates_enabled:
        return False
    message = f"{summary}. {_REPORT_REQUEST}"
    if strict:
        raise GateCheckError(message)
    _warn_failure(message)
    return True


def enforce_checks(reader_checks: Sequence[ReaderCheck], *, strict: bool) -> bool:
    """Report the applied checks of these readers that failed, naming each failed reader.

    On a strict save the failure is raised, carrying every one of the readers' checks so that a
    report can show them, and on any other save it is warned about with that same message.

    Returns:
        Whether a failure was warned about, which is False on a strict save and whenever
        every applied check passed.

    Raises:
        ReaderCheckError: An applied check failed and `strict` is True.

    Warns:
        ReaderCheckWarning: An applied check failed and `strict` is False.
    """
    summaries = [
        summary
        for reader_check in reader_checks
        if (summary := _failure_summary(reader_check.reader, reader_check.gates)) is not None
    ]
    if not summaries or not _gates_enabled:
        return False
    message = f"{'. '.join(summaries)}. {_REPORT_REQUEST}"
    if strict:
        raise GateCheckError(message, tuple(reader_checks))
    _warn_failure(message)
    return True


# How one reader fared: the type of `ReaderValidation.status`, named so that a caller can
# declare it. "ok" is a table read with every applied check passed, "failed" a check that did
# not pass, and "error" another fmsave error raised while reading.
type ReaderStatus = Literal["ok", "failed", "error"]


@dataclass(frozen=True, slots=True)
class ReaderValidation:
    """How one reader fared in `validate_save`.

    A reader is "failed" when a check of its own did not pass, and it is the only one reported
    so: the readers that join through it read the table it returned and are judged on their own
    checks.

    A save opened with `strict=True` is reported differently, because a failed check stops the
    reader there and everything downstream of it with it. Players, contracts and suspensions
    are decoded in one pass, so when a check of any of the three fails, all three are reported
    "failed" and none of their tables is read, and each of them still lists its own gates: a
    reader can be "failed" while every one of its own gates passed. Fixtures, league tables,
    competition rules and stadiums share the one streamed pass over the span the same way, and
    are reported together when that pass itself is what failed. Four more pairs share a decode
    in the same way: finances with sponsorships, staff with staff lists, training with
    mentoring, and tactics with set pieces. A structural failure spreads the same way on any
    save, since no mode reads a table from a decode that produced none.

    Attributes:
        reader: The reader: "clubs", "players", "contracts", "suspensions", "managed_clubs",
            "stages", "competitions", "fixtures", "league_tables", "transfer_windows",
            "competition_rules", "player_match_stats", "player_season_stats",
            "player_season_history", "stadiums",
            "finances", "sponsorships", "affiliates", "job_vacancies", "staff", "staff_lists",
            "injury_types", "injuries", "training", "mentoring", "tactics", "set_pieces" or
            "facilities".
        status: "ok" when the reader returned its table and every applied check of its own
            passed, "failed" when a check did not, and "error" when it raised another fmsave
            error.
        record_count: How many records the reader decoded, or None when it did not get far
            enough to count them.
        gates: The reader's checks, in a fixed order; empty when the reader has no checks of
            its own, as the managed-club reader does not, or when it did not get far enough.
        coverage: The table's coverage (the share of non-None values per column); empty
            unless the status is "ok".
        anomalies: Counts of records the reader decoded but flags, such as unresolved teams.
    """

    reader: str
    status: ReaderStatus
    record_count: int | None
    gates: tuple[GateResult, ...]
    coverage: Mapping[str, float]
    anomalies: Mapping[str, int]

    def to_json_dict(self) -> dict[str, object]:
        """The reader's outcome as a JSON-ready dict."""
        return {
            "reader": self.reader,
            "status": self.status,
            "record_count": self.record_count,
            "gates": [gate.to_json_dict() for gate in self.gates],
            "coverage": dict(self.coverage),
            "anomalies": dict(self.anomalies),
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """What `validate_save` found, holding no names, uids or other values from the save.

    Attributes:
        fmsave_version: The fmsave version.
        python_version: The Python version.
        os: The operating system name, for example "Linux".
        game: Game edition, for example "FM26".
        build: Version and build that last wrote the save.
        known_build: Whether fmsave has a full set of layout tables for this build.
        section_schemas: Schema number of every named section.
        readers: Each reader's outcome, in the order they ran.
        field_statuses: Whether each public field's meaning is "verified" or "unconfirmed".
    """

    fmsave_version: str
    python_version: str
    os: str
    game: str
    build: str
    known_build: bool
    section_schemas: Mapping[str, int]
    readers: tuple[ReaderValidation, ...]
    field_statuses: Mapping[str, str]

    def to_json_dict(self) -> dict[str, object]:
        """The report as a JSON-ready dict."""
        return {
            "fmsave_version": self.fmsave_version,
            "python_version": self.python_version,
            "os": self.os,
            "game": self.game,
            "build": self.build,
            "known_build": self.known_build,
            "section_schemas": dict(self.section_schemas),
            "readers": [reader.to_json_dict() for reader in self.readers],
            "field_statuses": dict(self.field_statuses),
        }


def _completed_validation(
    reader_name: str,
    record_count: int,
    coverage: Mapping[str, float],
    reader_check: ReaderCheck | None,
) -> ReaderValidation:
    """A reader that returned its table: "failed" when a check of its own did not pass.

    On a save opened without `strict=True` a failed check no longer stops the reader, so this
    is where most "failed" rows come from. The check has already been evaluated and kept beside
    the table, so the report reads the result off it rather than making a reader raise to find
    out. Coverage is left out of a failed row, as it is of one that raised.
    """
    gates = () if reader_check is None else reader_check.gates
    failed = any(gate.applied and not gate.passed for gate in gates)
    return ReaderValidation(
        reader_name,
        "failed" if failed else "ok",
        record_count,
        gates,
        _NO_COVERAGE if failed else coverage,
        _NO_ANOMALIES if reader_check is None else reader_check.anomalies,
    )


def _unsuccessful_validation(reader_name: str, error: FmsaveError) -> ReaderValidation:
    if not isinstance(error, ReaderCheckError):
        return ReaderValidation(reader_name, "error", None, (), _NO_COVERAGE, _NO_ANOMALIES)
    carried_checks = error.checks if isinstance(error, GateCheckError) else ()
    for reader_check in carried_checks:
        if reader_check.reader == reader_name:
            return ReaderValidation(
                reader_name,
                "failed",
                reader_check.record_count,
                reader_check.gates,
                _NO_COVERAGE,
                reader_check.anomalies,
            )
    return ReaderValidation(reader_name, "failed", None, (), _NO_COVERAGE, _NO_ANOMALIES)


def validate_save(career_save: Save) -> ValidationReport:
    """Run every reader on a save and report how each fared.

    Readers run in the order clubs, players, contracts, suspensions, managed clubs, stages,
    competitions, fixtures, league tables, transfer windows, competition rules, per-match
    player stats, stadiums, finances, sponsorships, affiliates, job vacancies, staff, staff
    lists, injury types, injury history, training, mentoring, tactics, set pieces, club
    facilities. The order puts each reader after the ones whose work it reuses, so a shared
    decode that fails is reported where it failed: stadiums follow the fixtures whose calendar
    they read, injury types precede the injury history that names its types, and the two
    readers of each shared pass sit side by side. A reader whose checks fail is reported
    "failed" with its checks, and one that raises another fmsave error is reported "error"
    without the error's text; the remaining readers still run. The report holds only structural
    facts, counts and rates, never names, uids or other values from the save.

    Readers run here exactly as they would for any other caller, with their warnings suppressed
    for the length of the run: this report lists every check each reader ran, so a warning
    beside it would only repeat what it already says. Running them leaves the save no different
    from how a caller who read those tables himself would leave it. On a save opened the
    default way nothing raises for a failed check, so every table this decodes is kept: the
    reader calls a caller makes afterwards are free of charge, and say nothing further about a
    check this report has already reported.

    Some readers share one decode: the players, contracts and suspensions of the player pass,
    the fixtures, league tables, competition rules and stadiums that all need the one streamed
    pass over the span, and the finance, staff, training and tactics pairs, each built by one
    pass of its own. When that shared decode raises before it finishes, its error is reported
    for every reader of the pass and the decode is not attempted again, so the span is streamed
    once however many of its readers report it. A reader that failed after its pass had been
    decoded failed on its own, and the others still run.

    Raises:
        SaveClosedError: The save is closed.
    """
    if career_save.closed:
        raise closed_save_error()
    save_info = career_save.info
    reader_tables = (
        (CLUBS_READER, career_save.clubs),
        (PLAYERS_READER, career_save.players),
        (CONTRACTS_READER, career_save.contracts),
        (SUSPENSIONS_READER, career_save.suspensions),
        (MANAGED_CLUBS_READER, career_save.managed_clubs),
        (STAGES_READER, career_save.stages),
        (COMPETITIONS_READER, career_save.competitions),
        (FIXTURES_READER, career_save.fixtures),
        (LEAGUE_TABLES_READER, career_save.league_tables),
        (TRANSFER_WINDOWS_READER, career_save.transfer_windows),
        (COMPETITION_RULES_READER, career_save.competition_rules),
        (PLAYER_MATCH_STATS_READER, career_save.player_match_stats),
        (SEASON_STATS_READER, career_save.player_season_stats),
        (SEASON_HISTORY_READER, career_save.player_season_history),
        (STADIUMS_READER, career_save.stadiums),
        (FINANCES_READER, career_save.finances),
        (SPONSORSHIPS_READER, career_save.sponsorships),
        (AFFILIATES_READER, career_save.affiliates),
        (JOB_VACANCIES_READER, career_save.job_vacancies),
        (STAFF_READER, career_save.staff),
        (STAFF_LISTS_READER, career_save.staff_lists),
        (INJURY_TYPES_READER, career_save.injury_types),
        (INJURIES_READER, career_save.injuries),
        (TRAINING_READER, career_save.training),
        (MENTORING_READER, career_save.mentoring),
        (TACTICS_READER, career_save.tactics),
        (SET_PIECES_READER, career_save.set_pieces),
        (FACILITIES_READER, career_save.facilities),
    )
    validations: list[ReaderValidation] = []
    failed_passes: dict[str, FmsaveError] = {}
    # A failed check warns rather than raising on a save opened the default way, and this
    # report lists every check each reader ran: a warning beside it would only repeat what the
    # report already says, and would make `fmsave validate` noisiest on exactly the saves it
    # exists to diagnose. The readers run as they would for any other caller, so a run leaves
    # nothing behind that changes how the save reads afterwards.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ReaderCheckWarning)
        for reader_name, read_table in reader_tables:
            shared_pass = _READER_PASSES.get(reader_name)
            carried_error = None if shared_pass is None else failed_passes.get(shared_pass)
            if carried_error is not None:
                # The shared decode would run again only to raise the same error.
                validations.append(_unsuccessful_validation(reader_name, carried_error))
                continue
            try:
                table = read_table()
            except FmsaveError as error:
                # Only a failure of the shared decode itself is carried to the rest of its pass.
                # A reader that raised after that decode was kept failed on its own account: the
                # decode is cached, so the readers after it repeat none of it, and reporting them
                # failed would call a table unreadable that reads perfectly well. This is narrow on
                # purpose, and widening it to carry every failure of any reader of a pass would not
                # be the safe direction: it would report the competition rules unreadable because
                # the league tables missed a gate, which is a different wrong answer rather than a
                # cautious one. The span is still streamed once, because the case that costs a
                # second streaming is the one where nothing was cached, which is the case carried.
                if shared_pass is not None and not career_save._shared_pass_cached(shared_pass):  # pyright: ignore[reportPrivateUsage]
                    failed_passes[shared_pass] = error
                validations.append(_unsuccessful_validation(reader_name, error))
                continue
            reader_check = career_save._reader_check(reader_name)  # pyright: ignore[reportPrivateUsage]
            validations.append(
                _completed_validation(reader_name, len(table), table.coverage, reader_check)
            )
    return ValidationReport(
        fmsave_version=__version__,
        python_version=platform.python_version(),
        os=platform.system(),
        game=save_info.game,
        build=save_info.build,
        known_build=save_info.known_build,
        section_schemas=FrozenMapping(save_info.section_schemas),
        readers=tuple(validations),
        field_statuses=registered_statuses(),
    )
