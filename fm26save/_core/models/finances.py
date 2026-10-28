"""Club money: one row per club per month, and the sponsor contracts a club holds.

**Money is a whole number in the save's base currency, which is not the currency the game
displays.** One save's screens were read against its own stored values and every figure came
out at the same rate: the balance, the transfer and wage budgets, the wage bill and the
month's income and expenditure all display at about 1.157 times what is stored, the one rate
fitting each of them. A single rate across every money field of a career is what says the
stored unit is a unit of its own rather than the displayed currency. No save says which unit
that is, so **nothing here is converted** and no rate is applied.

The weekly fields are weekly amounts; every other money field is one month's amount, or a
balance at the end of a month.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import IntEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


class SponsorType(IntEnum):
    """What kind of sponsorship a contract is.

    Every code is UNKNOWN: the save groups its sponsorships into about twenty kinds, and no
    displayed label has pinned one of those codes yet.
    """

    UNKNOWN = -1


@dataclass(frozen=True, slots=True)
class FinanceMonth:
    """One club's money in one month.

    Attributes:
        club_uid: Uid of the club (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        month: First day of the month the row covers, worked out from the save's own date: the
            last row of a club is the month before the save's month, and a club's two oldest
            rows landed on the months its own finance screen labelled them with.
        balance: The club's balance at the end of the month. On most clubs whose series
            begins with the career, the oldest row instead holds the balance before that
            month's net: the next row's balance adds both months' nets to it.
        transfer_budget_allocated: A transfer figure with no confirmed meaning
            (unconfirmed). It is **not** the budget the board allocated: a club's own finances
            screen showed a budget well above this figure with almost none of it spent, and
            this figure is below transfer_budget_remaining on about a quarter of rows.
        transfer_budget_remaining: What is left of the transfer budget.
        wage_budget_weekly: The wage budget, per week; a club's screen showed this times 52.
        wage_payroll_weekly: The wages being paid, per week; likewise times 52 on the screen.
        income_excluding_transfers: The month's income other than transfer fees
            (unconfirmed).
        net_transfers: The month's transfer flow, **positive for a net spend** (unconfirmed).
        wage_bill: The month's wage expenditure (unconfirmed).
        net: The month's income less its expenditure.
        expenditure_excluding_transfers: The month's expenditure other than transfer fees
            (unconfirmed).
        total_income: The month's total income (unconfirmed).
        total_expenditure: The month's total expenditure (unconfirmed).
    """

    club_uid: int
    club_name: str
    month: date
    balance: int
    transfer_budget_allocated: int
    transfer_budget_remaining: int
    wage_budget_weekly: int
    wage_payroll_weekly: int
    income_excluding_transfers: int
    net_transfers: int
    wage_bill: int
    net: int
    expenditure_excluding_transfers: int
    total_income: int
    total_expenditure: int


@dataclass(frozen=True, slots=True)
class Sponsorship:
    """One sponsorship contract of one club, running or ended.

    Attributes:
        club_uid: Uid of the club (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        kind: What kind of sponsorship it is; every code is UNKNOWN (unconfirmed).
        start: The day the contract starts.
        end: The day it ends.
        total_value: The contract's whole value. On most running contracts it is the annual
            value times the contract's whole years.
        annual_value: What a running contract pays a year. A contract that has ended can
            still carry a non-zero annual value, often equal to its total value, so neither a
            zero nor a non-zero value says whether the contract is still running; compare
            `end` with the save's date for that.
        unknown: Numeric fields with no known meaning (unconfirmed).
    """

    club_uid: int
    club_name: str
    kind: CodedValue[SponsorType]
    start: date | None
    end: date | None
    total_value: int
    annual_value: int
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("flag10", "u15", "b17", "enum18", "b19")


# The wage budget and the payroll are verified against a club's own finances screen, which
# showed each of them as the weekly figure times 52. The month label is verified too: the two
# oldest rows of that club's series landed on the months the screen's history panel labelled,
# which is what the one-month lag predicts and what no other lag does.
register_field_statuses(
    FinanceMonth,
    verified=(
        "month",
        "balance",
        "transfer_budget_remaining",
        "wage_budget_weekly",
        "wage_payroll_weekly",
        "net",
    ),
    # The rest are read from known offsets whose meaning no displayed figure has pinned yet,
    # `transfer_budget_allocated` being the one a screen has ruled a meaning out for.
    unconfirmed=(
        "club_uid",
        "club_name",
        "transfer_budget_allocated",
        "income_excluding_transfers",
        "net_transfers",
        "wage_bill",
        "expenditure_excluding_transfers",
        "total_income",
        "total_expenditure",
    ),
)
register_field_statuses(
    Sponsorship,
    verified=("start", "end", "total_value", "annual_value"),
    unconfirmed=("club_uid", "club_name", "kind", "unknown"),
)
