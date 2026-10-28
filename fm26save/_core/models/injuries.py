"""Injury records: the names the game gives the injuries it can hand out, and who was hurt.

The names are the game's own text, as the save stores it, in the language the save was written
in. They are not in any section of the save: every per-match file the save holds carries one
copy of the table, so a save that holds no per-match file has no names at all. Some injury
codes have no entry in the table, so a code a player's injury carries need not be named here
and reads as no name at all. **fmsave ships no injury names of its own**, whatever a screen
displays for such a code, exactly as it ships no competition names.

The history is one table of two kinds of row. A `HISTORY` row is an injury the save remembers
happening: when it happened, and which team the person was at. A `TYPED` row carries the injury
type of a recent or current episode, and **its date is the day the player is expected back**
rather than the day he was hurt. The save keeps the history for about the last two years only.

**A `HISTORY` row is not a row of the game's Injury History tab.** That tab reads the
full-career store, which fmsave does not ship: it shows injuries from years outside this
rolling window, so the store here is the recent part of a career the tab shows whole.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


@dataclass(frozen=True, slots=True)
class InjuryType:
    """One named injury the game can hand out.

    Attributes:
        id: The code the save stores on an injury of this type (unconfirmed).
        name: The game's own name for the injury, in the language the save was written in
            (unconfirmed).
        unknown: Numeric fields with no known meaning: a flag byte, and a second id in an id
            space of its own (unconfirmed).
    """

    id: int
    name: str
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("flag", "second_id")


class InjuryRecordKind(StrEnum):
    """Which of the save's two injury stores a row came out of."""

    HISTORY = "history"
    TYPED = "typed"


class InjuryCause(IntEnum):
    """Whether an injury happened in training or in a match.

    Both stored codes are named, each from the cause a player's injury history displayed
    against rows carrying that exact code. The screen also shows a second line saying what the
    player was doing -- jumping, tackling, wear and tear -- and that detail is in no field
    fmsave reads: three different details share the training code alone.

    **Illness rows are the exception.** A row for an illness -- a virus, food poisoning, a
    cold -- displays a vocabulary of its own, such as a cause of "Non-soccer", and its stored
    codes do not follow this mapping. That is one measured counter-example, on an illness row,
    against agreement on every injury row checked.
    """

    UNKNOWN = -1
    IN_TRAINING = 0
    IN_MATCH = 1


class InjurySeverity(IntEnum):
    """How bad an injury was, in the game's own words.

    All four stored codes are named, each from the severity a player's injury history displayed
    against a dated row carrying that exact code.

    **Illness rows are the exception.** A row for an illness -- a virus, food poisoning, a
    cold -- displays a vocabulary of its own and its stored codes do not follow this mapping:
    one such row stores the code an injury displays as Moderate while the game shows it as
    Minor. That is one measured counter-example, on an illness row, against agreement on every
    injury row checked.
    """

    UNKNOWN = -1
    SLIGHT = 0
    MINOR = 1
    MODERATE = 2
    MAJOR = 3


@dataclass(frozen=True, slots=True)
class InjuryRecord:
    """One injury the save remembers, of either kind.

    Attributes:
        kind: Which store the row came from: HISTORY for an injury that happened, TYPED for a
            row carrying an injury type.
        player_uid: Uid of the person the row is stored against, or None when the save no
            longer keeps that person as a player, which is about one HISTORY row in twenty
            (unconfirmed).
        player_name: Denormalised display name of player_uid; None wherever player_uid is
            (unconfirmed).
        date: When the injury happened, on a HISTORY row. On a TYPED row it is the day the
            player is expected back rather than the day he was hurt, which is why it is often
            ahead of the in-game date; it is None when the save stores no date at all.
        team_id: Id of the team the person was registered with at the time, on a HISTORY row;
            None on every TYPED row, which carries no team.
        club_uid: Uid of the club that fields team_id, which for a team another club controls
            is the controlling club; None when no club lists that team and on every TYPED
            row.
        club_name: Denormalised full name of club_uid; None wherever club_uid is.
        team_slot: The team's slot in club_uid's team list, counting that club's own teams
            first and then the teams it controls; None wherever club_uid is (unconfirmed).
        type_id: The injury's type code, on a TYPED row; None on every HISTORY row, which
            carries no type.
        type_name: Denormalised name of type_id from `Save.injury_types`, None for the codes
            that table has no entry for and on every row of a save with no per-match file
            (unconfirmed).
        cause: Whether the injury happened in training or in a match, on a HISTORY row; None
            on every TYPED row. Both stored codes carry the cause a screen displayed for them,
            except on an illness row, which displays its own vocabulary.
        severity: How bad the injury was, on a HISTORY row; None on every TYPED row. All four
            stored codes carry the severity a screen displayed for them, except on an illness
            row, which displays its own vocabulary.
        unknown: Numeric fields with no known meaning, each present only on the kind of row
            that carries it: `r0` a byte that is 1 on every row of every save, `hi7_date` the
            time-slot bits of the row's date word, and, on a TYPED row, `r11` and `r12`
            (unconfirmed).
    """

    kind: InjuryRecordKind
    player_uid: int | None
    player_name: str | None
    date: datetime.date | None
    team_id: int | None
    club_uid: int | None
    club_name: str | None
    team_slot: int | None
    type_id: int | None
    type_name: str | None
    cause: CodedValue[InjuryCause] | None
    severity: CodedValue[InjurySeverity] | None
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("r0", "r11", "r12", "hi7_date")


# The id is the space the typed injury records use, which is measured rather than displayed;
# it becomes verified once an in-game screen names one of these codes.
register_field_statuses(InjuryType, unconfirmed=("id", "name", "unknown"))
# The person link is the stored index plus one, which is measured against the player records
# rather than shown anywhere, and `type_name` is only as good as `InjuryType.name` it copies.
# The cause and the severity are verified because a player's injury history displayed the cause
# of both stored codes and the severity of all four against dated rows carrying them.
register_field_statuses(
    InjuryRecord,
    verified=(
        "kind",
        "date",
        "team_id",
        "club_uid",
        "club_name",
        "type_id",
        "cause",
        "severity",
    ),
    unconfirmed=(
        "player_uid",
        "player_name",
        "team_slot",
        "type_name",
        "unknown",
    ),
)
