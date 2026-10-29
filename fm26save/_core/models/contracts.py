"""Contract records: the chain of registrations, the terms agreed in them and their clauses.

A player's contract is assembled from a chain of registration records (one per club a
player has been registered to, oldest first), each carrying a wage and a start date, and
some of them the terms agreed as well: an end date, a squad status, a contract type and the
clauses. When no chain record gives its terms up, the player's own record can still supply a
start or an end date. See `readers/contracts.py` for the assembly rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import IntEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue, ContractEndSource


class SquadStatus(IntEnum):
    """The squad status agreed in a player's contract, as shown on the contract screen.

    It is the role the club agreed to, not a record of how much the player actually plays: a
    player on CUP_GOALKEEPER terms, for example, can still make league appearances all
    season. A code is named only where an in-game label confirms that exact code; a code an
    outside name table would name is not named on that basis alone. Every code that is not
    named is UNKNOWN and keeps its raw number.

    The game offers two sets of labels, one for goalkeepers and one for everyone else, and
    they do not share every code. FIRST_CHOICE_GOALKEEPER, CUP_GOALKEEPER,
    DOMESTIC_CUP_GOALKEEPER, CONTINENTAL_CUP_GOALKEEPER, BACKUP and
    GOALKEEPER_EMERGENCY_BACKUP are offered only for goalkeepers, and every holder of them
    is one. EMERGENCY_BACKUP and GOALKEEPER_EMERGENCY_BACKUP are separate codes that the
    game displays with the same words, "Emergency Backup", one for outfield players and one
    for goalkeepers, so the code says which list the status came from.

    BREAKTHROUGH_PROSPECT, FUTURE_PROSPECT and YOUNGSTER are not in either list: they are
    youth statuses the senior contract screen does not offer.
    """

    UNKNOWN = -1
    STAR_PLAYER = 1
    IMPORTANT_PLAYER = 2
    REGULAR_STARTER = 3
    SQUAD_PLAYER = 4
    IMPACT_SUB = 5
    FRINGE_PLAYER = 7
    EMERGENCY_BACKUP = 9
    BREAKTHROUGH_PROSPECT = 10
    FUTURE_PROSPECT = 11
    YOUNGSTER = 13
    B_TEAM_REGULAR = 14
    FIRST_CHOICE_GOALKEEPER = 15
    CUP_GOALKEEPER = 16
    DOMESTIC_CUP_GOALKEEPER = 17
    CONTINENTAL_CUP_GOALKEEPER = 18
    BACKUP = 20
    GOALKEEPER_EMERGENCY_BACKUP = 21
    SURPLUS_TO_REQUIREMENTS = 22


class ContractType(IntEnum):
    """A player's contract type code."""

    UNKNOWN = -1
    FULL_TIME = 1
    YOUTH = 3


class ClauseKind(IntEnum):
    """A contract clause's kind.

    Only kinds whose meaning is confirmed in game are named; every other code is UNKNOWN and
    keeps its raw number. Each code is a distinct kind. MINIMUM_FEE_RELEASE_DOMESTIC (0x12)
    and MINIMUM_FEE_RELEASE_DOMESTIC_HIGHER_DIVISION (0x11) are separate clauses the game
    words differently, "Minimum Fee Release Clause (Domestic)" and "Minimum Fee Release
    Clause (Domestic Clubs in Higher Division)"; no contract in the corpus carries both.

    RELEGATION_RELEASE and NON_PROMOTION_RELEASE are the clauses the game calls a relegation
    release clause and a non promotion release clause, and each one's value is a release fee
    like the other release kinds. Neither ever carries a parameter.

    A clause's value is the release fee for MINIMUM_FEE_RELEASE, RELEGATION_RELEASE,
    NON_PROMOTION_RELEASE, MINIMUM_FEE_RELEASE_FOREIGN, MINIMUM_FEE_RELEASE_DOMESTIC and
    MINIMUM_FEE_RELEASE_DOMESTIC_HIGHER_DIVISION, and the amount paid for APPEARANCE_FEE,
    SHUTOUT_BONUS, INTERNATIONAL_CAP_BONUS, UNUSED_SUBSTITUTE_FEE and
    SEASONAL_LANDMARK_COMBINED_GOALS_AND_ASSISTS. Every clause of those kinds carries one.
    TOP_DIVISION_RELEGATION_SALARY_DROP and OPTIONAL_EXTENSION_BY_CLUB carry a parameter
    instead and no value.

    A clause's parameter is a percentage for TOP_DIVISION_RELEGATION_SALARY_DROP, years for
    OPTIONAL_EXTENSION_BY_CLUB, the number of goals plus assists that earns the bonus for
    SEASONAL_LANDMARK_COMBINED_GOALS_AND_ASSISTS, and days to expiry from the contract start
    for MINIMUM_FEE_RELEASE_DOMESTIC and MINIMUM_FEE_RELEASE_DOMESTIC_HIGHER_DIVISION (None
    means no expiry). A minority of MINIMUM_FEE_RELEASE clauses carry a parameter too, and
    what it holds there is not confirmed.
    """

    UNKNOWN = -1
    MINIMUM_FEE_RELEASE = 0x00
    RELEGATION_RELEASE = 0x01
    NON_PROMOTION_RELEASE = 0x02
    TOP_DIVISION_RELEGATION_SALARY_DROP = 0x0F
    MINIMUM_FEE_RELEASE_FOREIGN = 0x10
    MINIMUM_FEE_RELEASE_DOMESTIC_HIGHER_DIVISION = 0x11
    MINIMUM_FEE_RELEASE_DOMESTIC = 0x12
    OPTIONAL_EXTENSION_BY_CLUB = 0x16
    APPEARANCE_FEE = 0x20
    SHUTOUT_BONUS = 0x22
    INTERNATIONAL_CAP_BONUS = 0x25
    UNUSED_SUBSTITUTE_FEE = 0x26
    SEASONAL_LANDMARK_COMBINED_GOALS_AND_ASSISTS = 0x29


@dataclass(frozen=True, slots=True)
class Clause:
    """One clause attached to a contract, such as a release fee, an extension option or a bonus.

    Every named kind is confirmed in game, and so is what a clause's value holds for each of
    them (see ClauseKind). A status covers a field across every kind, so parameter still ships
    unconfirmed: a minority of MINIMUM_FEE_RELEASE clauses carry one whose meaning no in-game
    reading pins.

    Attributes:
        kind: The clause's kind.
        parameter: The clause's parameter, whose meaning depends on kind; None when the
            save stores no parameter (unconfirmed).
        value: The clause's money value, in the save's own money unit and not converted;
            None when the save stores no value.
    """

    kind: CodedValue[ClauseKind]
    parameter: int | None
    value: int | None


@dataclass(frozen=True, slots=True)
class ContractChainEntry:
    """One record in a player's registration chain.

    Attributes:
        club_uid: Uid of the contracting club, or None when the team does not resolve
            (unconfirmed).
        club_name: Denormalised name of club_uid (unconfirmed).
        team_id: Id of the contracting team, exactly as stored (unconfirmed).
        wage: Weekly wage, in the save's base currency (unconfirmed).
        start: Start date of this spell (unconfirmed).
        end: End date from this record's own terms, or None when it gives no terms up or
            stores no end.
        has_terms: Whether this record carries the terms agreed in it: an end date, a squad
            status, a contract type and the clauses. A record that does not is still a spell
            at a club, with its wage and its start date (unconfirmed).
    """

    club_uid: int | None
    club_name: str | None
    team_id: int
    wage: int
    start: date | None
    end: date | None
    has_terms: bool


@dataclass(frozen=True, slots=True)
class Contract:
    """A player's contract as it stands at the save's in-game date.

    Every field below that a chain record fills comes from one record: the contract in
    effect, which is the record at the player's own club that has started and has not
    ended, or else the record with the latest start on or before the in-game date. Records
    that start later are agreed future moves, such as pre-contracts and completed transfers
    that take effect later; they stay in `chain` but never fill these fields. When no record
    has started, those fields are None or empty and `chain` still lists every record.

    Attributes:
        player_uid: Uid of the player this contract belongs to (unconfirmed).
        player_name: Denormalised name of player_uid (unconfirmed).
        club_uid: Uid of the contracting club of the record in effect, or None when no
            record is in effect or its team does not resolve (unconfirmed).
        club_name: Denormalised name of club_uid (unconfirmed).
        team_id: Id of the contracting team of the record in effect, or None
            (unconfirmed).
        wage: Weekly wage from the record in effect, in the save's base currency
            (unconfirmed).
        start: Contract start date, from the record in effect (unconfirmed).
        end: Contract end date.
        end_source: Where end was read from.
        squad_status: Squad status from the terms of the record in effect, the role agreed in
            the contract rather than how much the player plays, or None when that record
            gives no terms up.
        kind: The contract's type from the terms of the record in effect, or None when it
            gives no terms up.
        clauses: Clauses from the terms of the record in effect, or () when it gives no terms
            up.
        on_loan: Whether the player is on loan from the club of the contract in effect:
            True when he is registered with another club's team and the save holds a loan
            for him there that has not ended, False when it does not, and None when his
            club or the contract in effect is unknown. A player registered with a team his
            own club controls, such as a B team, is a player of that club, not on loan.
        loan_parent_club_uid: Uid of the club of the contract in effect when on_loan is
            True, else None. It is club_uid under another name, so it carries the same
            status (unconfirmed).
        loan_parent_club_name: Denormalised name of loan_parent_club_uid (unconfirmed).
        loan_start: Date the loan began when on_loan is True, else None. It is also None
            when the loan's stored start does not decode as a game date, which keeps an
            unreadable start from costing the player his loan; no save read so far holds
            such a loan.
        loan_end: Date the loan ends when on_loan is True, else None.
        event_count: Contract event count from the terms of the record in effect, or None
            (unconfirmed).
        chain: Every chain record, oldest first (unconfirmed).
        chain_club_uids: Uid of the contracting club for each chain record, in the same
            order as chain; None where the team does not resolve (unconfirmed).
        chain_club_names: Denormalised names for chain_club_uids, in the same order
            (unconfirmed).
        chain_club_uids_with_terms: Uids of the clubs of the chain records that carry their
            agreed terms and whose team resolves, in chain order (unconfirmed).
        chain_club_names_with_terms: Denormalised names for chain_club_uids_with_terms, in
            the same order (unconfirmed).
        unknown: Numeric fields with no known meaning, from the terms of the record in
            effect; a key is present only when its value was read (unconfirmed).
    """

    player_uid: int
    player_name: str | None
    club_uid: int | None
    club_name: str | None
    team_id: int | None
    wage: int | None
    start: date | None
    end: date | None
    end_source: ContractEndSource
    squad_status: CodedValue[SquadStatus] | None
    kind: CodedValue[ContractType] | None
    clauses: tuple[Clause, ...]
    on_loan: bool | None
    loan_parent_club_uid: int | None
    loan_parent_club_name: str | None
    loan_start: date | None
    loan_end: date | None
    event_count: int | None
    chain: tuple[ContractChainEntry, ...]
    chain_club_uids: tuple[int | None, ...]
    chain_club_names: tuple[str | None, ...]
    chain_club_uids_with_terms: tuple[int, ...]
    chain_club_names_with_terms: tuple[str | None, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = (
        "money_a",
        "money_b",
        "money_c",
        "e2",
        "e8",
        "e12",
        "e16",
        "e20",
        "e24",
        "e37",
        "e38",
        "e39",
    )

    @property
    def signing_or_loyalty_fee(self) -> int:
        """Signing or loyalty fee decoded from unknown['money_a']."""
        return self.unknown.get("money_a", 0)

    @property
    def agent_fee(self) -> int:
        """Agent commission fee decoded from unknown['money_b']."""
        return self.unknown.get("money_b", 0)

    @property
    def package_bonus(self) -> int:
        """Additional package bonus decoded from unknown['money_c']."""
        return self.unknown.get("money_c", 0)

    @property
    def option_or_reference_year(self) -> int | None:
        """Contract option or reference year decoded from unknown['e12'] (1900 is null-date sentinel)."""
        val = self.unknown.get("e12")
        return None if val is None or val <= 1900 else val


register_field_statuses(
    Clause,
    verified=("kind", "value"),
    unconfirmed=("parameter",),
)
# `end` is the same agreed-terms field Contract.end is taken from, and the contract end the
# game displays confirmed it; `start` has no displayed label behind it on either class.
register_field_statuses(
    ContractChainEntry,
    verified=("end",),
    unconfirmed=("club_uid", "club_name", "team_id", "wage", "start", "has_terms"),
)
register_field_statuses(
    Contract,
    verified=(
        "end",
        "end_source",
        "squad_status",
        "kind",
        "clauses",
        "on_loan",
        "loan_start",
        "loan_end",
    ),
    unconfirmed=(
        "player_uid",
        "player_name",
        "club_uid",
        "club_name",
        "team_id",
        "wage",
        "start",
        "loan_parent_club_uid",
        "loan_parent_club_name",
        "event_count",
        "chain",
        "chain_club_uids",
        "chain_club_names",
        "chain_club_uids_with_terms",
        "chain_club_names_with_terms",
        "unknown",
    ),
)
