"""Archived player statistics, with the same counts and rates as current-season rows."""

from __future__ import annotations

import dataclasses

from fm26save._core._status import field_status, register_field_statuses
from fm26save._core.models.season_stats import PlayerSeasonStats


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerSeasonHistory(PlayerSeasonStats):
    """One archived statistics line for a player and team.

    Inherits the statistics and computed rates of `PlayerSeasonStats`. The team is the
    archived team, which may differ from the player's current team. Goalkeeper fields use
    the player's current natural positions; the archive does not identify their past role.
    Imported history can omit detailed counts, so a stored zero does not prove no event
    occurred. Rows keep their stored order, which need not be chronological.

    Attributes:
        team_id: Archived team reference, or None for the missing-reference sentinel.
        season_year: Candidate season year; whether it identifies the start or end of a
            season is unknown (unconfirmed).
        competition_reference: Raw candidate competition reference, without a confirmed
            mapping to competition entities or database ids (unconfirmed).
    """

    season_year: int
    competition_reference: int


for _status in ("verified", "unconfirmed"):
    register_field_statuses(
        PlayerSeasonHistory,
        **{
            _status: tuple(
                name
                for name in (
                    *(field.name for field in dataclasses.fields(PlayerSeasonStats)),
                    *PlayerSeasonStats.COMPUTED_FIELDS,
                )
                if field_status(PlayerSeasonStats, name) == _status
            )
        },
    )
register_field_statuses(PlayerSeasonHistory, unconfirmed=("season_year", "competition_reference"))
