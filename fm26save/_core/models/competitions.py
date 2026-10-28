"""Competitions and the stages they are played in.

A competition is played as a sequence of stages: a league season is one stage, a cup is one
stage per round, and a two-legged tie is two stages sharing one round code rather than one
stage with a leg number. The stage table is the only route from a fixture, a league-table
group or a per-match record to a competition, so a stage id is the key every competition join
goes through.

Competition ids here belong to the stage id space, which `Suspension.competition_id` joins
too: a ban covering one competition names it by exactly this id.

The save stores no competition name table: the game renders competition names from its own
installed database, so `Competition.name` and every denormalised `competition_name` stay None
unless a name map is supplied.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


class CompetitionRound(IntEnum):
    """A stage's round in its competition, for the round codes whose meaning is confirmed.

    A code is named only where a round label the game itself displayed was matched to that
    exact code. Every other code is UNKNOWN and keeps its raw number in `CodedValue.raw`,
    including codes that look like they continue a named run: a meaning is never carried
    across from a neighbouring code, because a wrong name is silently wrong while a raw
    number is plainly incomplete. Most codes a save uses are therefore UNKNOWN, among them
    the codes group stages and the qualifying rounds use.

    A stage with no round at all reads as None rather than UNKNOWN: a league matchday and a
    league phase carry no round, and the matchday is a property of the fixture, not the stage.
    """

    UNKNOWN = -1
    THIRD_ROUND = 7
    FOURTH_ROUND = 8
    QUARTER_FINAL = 16
    SEMI_FINAL = 17
    FINAL = 19


@dataclass(frozen=True, slots=True)
class Stage:
    """One stage of one competition: a league season, a cup round, or one leg of a tie.

    Attributes:
        id: The stage id, which every fixture, league-table group and per-match record joins
            through.
        competition_id: Id of the competition this stage belongs to, in the stage id space;
            None when the row stores no competition, and None for the one out-of-band id every
            save carries, which is a marker rather than a competition.
        competition_name: Denormalised name of competition_id, which is None unless a name
            map is supplied, because the save stores no competition names (unconfirmed).
        group_id: Id of the group or section within the competition, or None when the stage
            has none.
        round: The stage's round, or None when the stage has no round, as a league matchday
            and a league phase do not. Codes with no confirmed meaning keep their raw number
            and are labelled UNKNOWN.
        previous_stage_id: The stage id the row claims comes before this one; None when the
            row stores the missing value. It equals `id - 1` on every row seen, and the
            reader's own row test requires that, so it is not independent evidence of a
            chain between stages (unconfirmed).
        unknown: Numeric fields with no known meaning. "s25" is data, not a sentinel: it
            takes small values on several hundred rows per save. "s29" is the missing value
            on almost every row and carries small numbers on the rest (unconfirmed).
    """

    id: int
    competition_id: int | None
    competition_name: str | None
    group_id: int | None
    round: CodedValue[CompetitionRound] | None
    previous_stage_id: int | None
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("s25", "s29")


@dataclass(frozen=True, slots=True)
class Competition:
    """One competition, as the stage table names it.

    Attributes:
        id: The competition id, in the stage id space (not the id space a suspension's
            competition id belongs to).
        database_id: The competition's id in the game's own editor database, which is stable
            across saves and is what an external name source is keyed on; None when the save
            holds no such link (unconfirmed).
        name: The competition's name, which is None unless a name map is supplied: the save
            stores no competition names, and fmsave ships none (unconfirmed).
        stage_ids: The ids of this competition's stages, in the order the stage table stores
            them, which is ascending on every save seen.
    """

    id: int
    database_id: int | None
    name: str | None
    stage_ids: tuple[int, ...]


register_field_statuses(
    Stage,
    verified=("id", "competition_id", "group_id", "round"),
    unconfirmed=("competition_name", "previous_stage_id", "unknown"),
)
register_field_statuses(
    Competition,
    verified=("id", "stage_ids"),
    unconfirmed=("database_id", "name"),
)
