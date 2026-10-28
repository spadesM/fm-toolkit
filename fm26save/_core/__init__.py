"""fmsave: read Football Manager 26 save files."""

from fm26save._core._errors import (
    AmbiguousNameError,
    CorruptSaveError,
    FmsaveError,
    FmsaveWarning,
    NotAFmSaveError,
    ReaderCheckError,
    ReaderCheckWarning,
    SaveChangedError,
    SaveClosedError,
    UnknownBuildWarning,
    UnsupportedGameError,
)
from fm26save._core._package import __version__
from fm26save._core._save import Save
from fm26save._core._save import open_save as open
from fm26save._core._status import FieldStatus, field_status
from fm26save._core.checks import (
    GateCheckError,
    GateResult,
    ReaderCheck,
    ReaderStatus,
    ReaderValidation,
    ValidationReport,
    validate_save,
)
from fm26save._core.models.affiliates import AffiliateGroup
from fm26save._core.models.clubs import Club, Team
from fm26save._core.models.common import CodedValue, ContractEndSource, TransferValueState
from fm26save._core.models.competitions import Competition, CompetitionRound, Stage
from fm26save._core.models.contracts import (
    Clause,
    ClauseKind,
    Contract,
    ContractChainEntry,
    ContractType,
    SquadStatus,
)
from fm26save._core.models.facilities import ClubFacilities, CorporateFacilities
from fm26save._core.models.finances import FinanceMonth, Sponsorship, SponsorType
from fm26save._core.models.fixtures import Fixture
from fm26save._core.models.injuries import (
    InjuryCause,
    InjuryRecord,
    InjuryRecordKind,
    InjurySeverity,
    InjuryType,
)
from fm26save._core.models.jobs import JobVacancy
from fm26save._core.models.league_tables import (
    LeagueTable,
    LeagueTableMatch,
    LeagueTableRow,
    LeagueTableSplit,
    MatchOutcome,
    MatchSide,
)
from fm26save._core.models.managed import ManagedClub
from fm26save._core.models.matches import MatchPosition, PlayerMatchStats
from fm26save._core.models.meta import SaveInfo, SectionInfo
from fm26save._core.models.players import (
    Ability,
    Attributes,
    Personality,
    Player,
    Positions,
    Reputation,
    Trait,
)
from fm26save._core.models.rules import (
    CompetitionRules,
    RulesBlockKind,
    RulesRound,
    TransferWindow,
)
from fm26save._core.models.season_history import PlayerSeasonHistory
from fm26save._core.models.season_stats import PlayerSeasonStats, SeasonStatsKind
from fm26save._core.models.stadiums import Stadium
from fm26save._core.models.staff import Staff, StaffAttributes, StaffList, StaffPreferences
from fm26save._core.models.suspensions import PlayerSuspension, Suspension, SuspensionScope
from fm26save._core.models.tactics import (
    Mentality,
    SetPieceRoutine,
    Tactic,
    TacticPosition,
    TacticSettingUnit,
    TacticSlot,
)
from fm26save._core.models.training import (
    MentoringGroup,
    TeamTraining,
    TrainingSchedule,
    TrainingWeek,
)
from fm26save._core.name_maps import read_competition_names
from fm26save._core.table import Table

OUTPUT_SCHEMA_VERSION = 2

__all__ = [
    "OUTPUT_SCHEMA_VERSION",
    "Ability",
    "AffiliateGroup",
    "AmbiguousNameError",
    "Attributes",
    "Clause",
    "ClauseKind",
    "Club",
    "ClubFacilities",
    "CodedValue",
    "Competition",
    "CompetitionRound",
    "CompetitionRules",
    "Contract",
    "ContractChainEntry",
    "ContractEndSource",
    "ContractType",
    "CorporateFacilities",
    "CorruptSaveError",
    "FieldStatus",
    "FinanceMonth",
    "Fixture",
    "FmsaveError",
    "FmsaveWarning",
    "GateCheckError",
    "GateResult",
    "InjuryCause",
    "InjuryRecord",
    "InjuryRecordKind",
    "InjurySeverity",
    "InjuryType",
    "JobVacancy",
    "LeagueTable",
    "LeagueTableMatch",
    "LeagueTableRow",
    "LeagueTableSplit",
    "ManagedClub",
    "MatchOutcome",
    "MatchPosition",
    "MatchSide",
    "Mentality",
    "MentoringGroup",
    "NotAFmSaveError",
    "Personality",
    "Player",
    "PlayerMatchStats",
    "PlayerSeasonHistory",
    "PlayerSeasonStats",
    "PlayerSuspension",
    "Positions",
    "ReaderCheck",
    "ReaderCheckError",
    "ReaderCheckWarning",
    "ReaderStatus",
    "ReaderValidation",
    "Reputation",
    "RulesBlockKind",
    "RulesRound",
    "Save",
    "SaveChangedError",
    "SaveClosedError",
    "SaveInfo",
    "SeasonStatsKind",
    "SectionInfo",
    "SetPieceRoutine",
    "SponsorType",
    "Sponsorship",
    "SquadStatus",
    "Stadium",
    "Staff",
    "StaffAttributes",
    "StaffList",
    "StaffPreferences",
    "Stage",
    "Suspension",
    "SuspensionScope",
    "Table",
    "Tactic",
    "TacticPosition",
    "TacticSettingUnit",
    "TacticSlot",
    "Team",
    "TeamTraining",
    "TrainingSchedule",
    "TrainingWeek",
    "Trait",
    "TransferValueState",
    "TransferWindow",
    "UnknownBuildWarning",
    "UnsupportedGameError",
    "ValidationReport",
    "__version__",
    "field_status",
    "open",
    "read_competition_names",
    "validate_save",
]
