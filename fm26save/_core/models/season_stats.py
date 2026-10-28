"""Season statistics: each player's stats for the current season.

A row covers one competition type for one team, like a row of the player profile's statistics
panel. `OVERALL` is the season total the squad screen shows.

Each row also has the rates the game shows, such as `expected_goals_per_90` and
`pass_completion_percent`. They are worked out from the counts when read, so they cost no
memory, and every export includes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses


def _per_90(count: float | None, minutes: int) -> float | None:
    return None if count is None or not minutes else count * 90 / minutes


def _percent(part: float | None, whole: float | None) -> float | None:
    return None if part is None or not whole else 100 * part / whole


class SeasonStatsKind(StrEnum):
    """The competition type a row covers, named after the player profile's statistics rows.

    `OVERALL` is "Overall (Club)", the season total. The two calendar-year kinds reset on
    1 January. Rows for another team the player played for this season use the first six kinds.
    """

    NON_COMPETITIVE = "non_competitive"
    LEAGUE = "league"
    CUP = "cup"
    CONTINENTAL = "continental"
    INTERNATIONAL = "international"
    OVERALL = "overall"
    CALENDAR_YEAR_OVERALL = "calendar_year_overall"
    CALENDAR_YEAR_INTERNATIONAL = "calendar_year_international"


@dataclass(frozen=True, slots=True)
class PlayerSeasonStats:
    """One player's stats for one competition type and one team this season.

    A competition type with no games has no row. Goalkeepers get `saves_held`, `saves_parried`,
    `saves_tipped` and `shots_on_target_faced`; everyone else gets
    `aerial_challenges_attempted`, `headers_won`, `open_play_crosses_completed`, `blocks` and
    `clearances`. The other set is None. A player counts as a goalkeeper when GK is one of
    their natural positions.

    Rates: most counts have a `_per_90` version (such as `goals_per_90`), plus
    `pass_completion_percent`, `cross_completion_percent`,
    `open_play_cross_completion_percent`, `headers_won_percent`, `tackle_completion_percent`,
    `shots_on_target_percent`, `conversion_percent`, `save_percent`,
    `expected_goals_per_shot` and `headers_lost_per_90`. A rate is None when there is nothing
    to divide by. `COMPUTED_FIELDS` lists them all.

    Attributes:
        player_uid: Uid of the player.
        player_name: Denormalised name of player_uid.
        kind: The competition type the row covers.
        team_id: The team the row is for: the player's current team, or another team they
            played for this season.
        club_uid: Uid of the club whose team list holds team_id, or None when no club lists it.
        club_name: Denormalised name of club_uid, or None when the team does not resolve.
        club_short_name: Denormalised short name of club_uid, or None when the team does not
            resolve.
        team_slot: The team's slot in its club's team list, 0 for the first entry, or None when
            the team does not resolve (unconfirmed).
        starts: Appearances from the start.
        substitute_appearances: Appearances from the bench.
        minutes: Minutes played.
        rated_appearances: Appearances the game gave a rating.
        average_rating: Average match rating, or None when no appearance was rated.
        player_of_the_match: Player of the match awards (unconfirmed).
        goals: Goals.
        assists: Assists.
        expected_goals: Expected goals (xG).
        non_penalty_expected_goals: Expected goals from shots other than penalties (npxG)
            (unconfirmed).
        expected_assists: Expected assists (xA).
        shots: Shots.
        shots_on_target: Shots on target.
        shots_outside_box: Shots from outside the box.
        goals_outside_box: Goals from outside the box (unconfirmed).
        free_kick_shots: Shots from free kicks (unconfirmed).
        penalties_taken: Penalties taken (unconfirmed).
        penalties_scored: Penalties scored (unconfirmed).
        passes_attempted: Passes attempted.
        passes_completed: Passes completed.
        progressive_passes: Progressive passes.
        key_passes: Key passes.
        open_play_key_passes: Key passes in open play.
        clear_cut_chances_created: Clear-cut chances created. The game's "chances created"
            figure counts the same thing.
        crosses_attempted: Crosses attempted.
        crosses_completed: Crosses completed.
        open_play_crosses_attempted: Crosses attempted in open play (unconfirmed).
        open_play_crosses_completed: Crosses completed in open play; None on a goalkeeper's
            line (unconfirmed).
        dribbles: Dribbles made.
        offsides: Offsides.
        distance_km: Distance covered, in kilometres.
        high_intensity_sprints: High intensity sprints.
        aerial_challenges_attempted: Aerial challenges attempted; None for a goalkeeper.
        headers_won: Headers won; None for a goalkeeper.
        key_headers: Key headers (unconfirmed).
        tackles_attempted: Tackles attempted.
        tackles_completed: Tackles completed.
        key_tackles: Key tackles (unconfirmed).
        interceptions: Interceptions.
        possession_won: Times the player won possession.
        possession_lost: Times the player lost possession (unconfirmed).
        pressures_attempted: Pressures attempted.
        pressures_completed: Pressures completed.
        blocks: Blocks; None for a goalkeeper (unconfirmed).
        shots_blocked: Shots blocked while defending (unconfirmed).
        clearances: Clearances; None for a goalkeeper.
        fouls_made: Fouls made.
        fouls_against: Fouls suffered.
        yellow_cards: Yellow cards.
        red_cards: Red cards (unconfirmed).
        mistakes_leading_to_goal: Mistakes leading to a goal (unconfirmed).
        clean_sheets: Clean sheets; 0 for an outfield player (unconfirmed).
        goals_allowed: Goals conceded as goalkeeper; 0 for an outfield player (unconfirmed).
        saves_held: Saves held; None for an outfield player (unconfirmed).
        saves_parried: Saves parried; None for an outfield player (unconfirmed).
        saves_tipped: Saves tipped; None for an outfield player (unconfirmed).
        shots_on_target_faced: Shots on target faced as goalkeeper; None for an outfield player
            (unconfirmed).
        expected_goals_prevented: Expected goals prevented (xGP); negative when a goalkeeper
            conceded more than expected (unconfirmed).
    """

    player_uid: int
    player_name: str | None
    kind: SeasonStatsKind
    team_id: int | None
    club_uid: int | None
    club_name: str | None
    club_short_name: str | None
    team_slot: int | None
    starts: int
    substitute_appearances: int
    minutes: int
    rated_appearances: int
    average_rating: float | None
    player_of_the_match: int
    goals: int
    assists: int
    expected_goals: float
    non_penalty_expected_goals: float
    expected_assists: float
    shots: int
    shots_on_target: int
    shots_outside_box: int
    goals_outside_box: int
    free_kick_shots: int
    penalties_taken: int
    penalties_scored: int
    passes_attempted: int
    passes_completed: int
    progressive_passes: int
    key_passes: int
    open_play_key_passes: int
    clear_cut_chances_created: int
    crosses_attempted: int
    crosses_completed: int
    open_play_crosses_attempted: int
    open_play_crosses_completed: int | None
    dribbles: int
    offsides: int
    distance_km: float
    high_intensity_sprints: int
    aerial_challenges_attempted: int | None
    headers_won: int | None
    key_headers: int
    tackles_attempted: int
    tackles_completed: int
    key_tackles: int
    interceptions: int
    possession_won: int
    possession_lost: int
    pressures_attempted: int
    pressures_completed: int
    blocks: int | None
    shots_blocked: int
    clearances: int | None
    fouls_made: int
    fouls_against: int
    yellow_cards: int
    red_cards: int
    mistakes_leading_to_goal: int
    clean_sheets: int
    goals_allowed: int
    saves_held: int | None
    saves_parried: int | None
    saves_tipped: int | None
    shots_on_target_faced: int | None
    expected_goals_prevented: float

    COMPUTED_FIELDS: ClassVar[tuple[str, ...]] = (
        "pass_completion_percent",
        "cross_completion_percent",
        "open_play_cross_completion_percent",
        "headers_won_percent",
        "tackle_completion_percent",
        "shots_on_target_percent",
        "conversion_percent",
        "save_percent",
        "expected_goals_per_shot",
        "goals_per_90",
        "assists_per_90",
        "expected_goals_per_90",
        "non_penalty_expected_goals_per_90",
        "expected_assists_per_90",
        "expected_goals_prevented_per_90",
        "shots_per_90",
        "shots_on_target_per_90",
        "shots_outside_box_per_90",
        "passes_attempted_per_90",
        "passes_completed_per_90",
        "progressive_passes_per_90",
        "key_passes_per_90",
        "open_play_key_passes_per_90",
        "clear_cut_chances_created_per_90",
        "crosses_attempted_per_90",
        "crosses_completed_per_90",
        "open_play_crosses_attempted_per_90",
        "open_play_crosses_completed_per_90",
        "dribbles_per_90",
        "distance_km_per_90",
        "high_intensity_sprints_per_90",
        "aerial_challenges_attempted_per_90",
        "headers_won_per_90",
        "headers_lost_per_90",
        "key_headers_per_90",
        "tackles_completed_per_90",
        "key_tackles_per_90",
        "interceptions_per_90",
        "possession_won_per_90",
        "possession_lost_per_90",
        "pressures_attempted_per_90",
        "pressures_completed_per_90",
        "blocks_per_90",
        "shots_blocked_per_90",
        "clearances_per_90",
        "goals_allowed_per_90",
    )

    # Rates the game shows, worked out from the counts on access so they cost nothing per row.
    # Each is None when there is nothing to divide by or the count does not apply.
    @property
    def pass_completion_percent(self) -> float | None:
        """Passes completed, as a percentage of passes attempted."""
        return _percent(self.passes_completed, self.passes_attempted)

    @property
    def cross_completion_percent(self) -> float | None:
        """Crosses completed, as a percentage of crosses attempted."""
        return _percent(self.crosses_completed, self.crosses_attempted)

    @property
    def open_play_cross_completion_percent(self) -> float | None:
        """Open-play crosses completed, as a percentage of those attempted."""
        return _percent(self.open_play_crosses_completed, self.open_play_crosses_attempted)

    @property
    def headers_won_percent(self) -> float | None:
        """Headers won, as a percentage of aerial challenges attempted."""
        return _percent(self.headers_won, self.aerial_challenges_attempted)

    @property
    def tackle_completion_percent(self) -> float | None:
        """Tackles completed, as a percentage of tackles attempted."""
        return _percent(self.tackles_completed, self.tackles_attempted)

    @property
    def shots_on_target_percent(self) -> float | None:
        """Shots on target, as a percentage of shots."""
        return _percent(self.shots_on_target, self.shots)

    @property
    def conversion_percent(self) -> float | None:
        """Goals, as a percentage of shots."""
        return _percent(self.goals, self.shots)

    @property
    def save_percent(self) -> float | None:
        """Saves held, parried and tipped, as a percentage of shots on target faced."""
        if self.saves_held is None or self.saves_parried is None or self.saves_tipped is None:
            return None
        saves = self.saves_held + self.saves_parried + self.saves_tipped
        return _percent(saves, self.shots_on_target_faced)

    @property
    def expected_goals_per_shot(self) -> float | None:
        """Expected goals per shot."""
        return self.expected_goals / self.shots if self.shots else None

    @property
    def goals_per_90(self) -> float | None:
        """Goals per 90 minutes."""
        return _per_90(self.goals, self.minutes)

    @property
    def assists_per_90(self) -> float | None:
        """Assists per 90 minutes."""
        return _per_90(self.assists, self.minutes)

    @property
    def expected_goals_per_90(self) -> float | None:
        """Expected goals per 90 minutes."""
        return _per_90(self.expected_goals, self.minutes)

    @property
    def non_penalty_expected_goals_per_90(self) -> float | None:
        """Non-penalty expected goals per 90 minutes."""
        return _per_90(self.non_penalty_expected_goals, self.minutes)

    @property
    def expected_assists_per_90(self) -> float | None:
        """Expected assists per 90 minutes."""
        return _per_90(self.expected_assists, self.minutes)

    @property
    def expected_goals_prevented_per_90(self) -> float | None:
        """Expected goals prevented per 90 minutes."""
        return _per_90(self.expected_goals_prevented, self.minutes)

    @property
    def shots_per_90(self) -> float | None:
        """Shots per 90 minutes."""
        return _per_90(self.shots, self.minutes)

    @property
    def shots_on_target_per_90(self) -> float | None:
        """Shots on target per 90 minutes."""
        return _per_90(self.shots_on_target, self.minutes)

    @property
    def shots_outside_box_per_90(self) -> float | None:
        """Shots from outside the box per 90 minutes."""
        return _per_90(self.shots_outside_box, self.minutes)

    @property
    def passes_attempted_per_90(self) -> float | None:
        """Passes attempted per 90 minutes."""
        return _per_90(self.passes_attempted, self.minutes)

    @property
    def passes_completed_per_90(self) -> float | None:
        """Passes completed per 90 minutes."""
        return _per_90(self.passes_completed, self.minutes)

    @property
    def progressive_passes_per_90(self) -> float | None:
        """Progressive passes per 90 minutes."""
        return _per_90(self.progressive_passes, self.minutes)

    @property
    def key_passes_per_90(self) -> float | None:
        """Key passes per 90 minutes."""
        return _per_90(self.key_passes, self.minutes)

    @property
    def open_play_key_passes_per_90(self) -> float | None:
        """Open-play key passes per 90 minutes."""
        return _per_90(self.open_play_key_passes, self.minutes)

    @property
    def clear_cut_chances_created_per_90(self) -> float | None:
        """Clear-cut chances created per 90 minutes."""
        return _per_90(self.clear_cut_chances_created, self.minutes)

    @property
    def crosses_attempted_per_90(self) -> float | None:
        """Crosses attempted per 90 minutes."""
        return _per_90(self.crosses_attempted, self.minutes)

    @property
    def crosses_completed_per_90(self) -> float | None:
        """Crosses completed per 90 minutes."""
        return _per_90(self.crosses_completed, self.minutes)

    @property
    def open_play_crosses_attempted_per_90(self) -> float | None:
        """Open-play crosses attempted per 90 minutes."""
        return _per_90(self.open_play_crosses_attempted, self.minutes)

    @property
    def open_play_crosses_completed_per_90(self) -> float | None:
        """Open-play crosses completed per 90 minutes."""
        return _per_90(self.open_play_crosses_completed, self.minutes)

    @property
    def dribbles_per_90(self) -> float | None:
        """Dribbles per 90 minutes."""
        return _per_90(self.dribbles, self.minutes)

    @property
    def distance_km_per_90(self) -> float | None:
        """Distance covered in kilometres per 90 minutes."""
        return _per_90(self.distance_km, self.minutes)

    @property
    def high_intensity_sprints_per_90(self) -> float | None:
        """High intensity sprints per 90 minutes."""
        return _per_90(self.high_intensity_sprints, self.minutes)

    @property
    def aerial_challenges_attempted_per_90(self) -> float | None:
        """Aerial challenges attempted per 90 minutes."""
        return _per_90(self.aerial_challenges_attempted, self.minutes)

    @property
    def headers_won_per_90(self) -> float | None:
        """Headers won per 90 minutes."""
        return _per_90(self.headers_won, self.minutes)

    @property
    def headers_lost_per_90(self) -> float | None:
        """Aerial challenges lost per 90 minutes."""
        if self.aerial_challenges_attempted is None or self.headers_won is None:
            return None
        return _per_90(self.aerial_challenges_attempted - self.headers_won, self.minutes)

    @property
    def key_headers_per_90(self) -> float | None:
        """Key headers per 90 minutes."""
        return _per_90(self.key_headers, self.minutes)

    @property
    def tackles_completed_per_90(self) -> float | None:
        """Tackles completed per 90 minutes."""
        return _per_90(self.tackles_completed, self.minutes)

    @property
    def key_tackles_per_90(self) -> float | None:
        """Key tackles per 90 minutes."""
        return _per_90(self.key_tackles, self.minutes)

    @property
    def interceptions_per_90(self) -> float | None:
        """Interceptions per 90 minutes."""
        return _per_90(self.interceptions, self.minutes)

    @property
    def possession_won_per_90(self) -> float | None:
        """Possession won per 90 minutes."""
        return _per_90(self.possession_won, self.minutes)

    @property
    def possession_lost_per_90(self) -> float | None:
        """Possession lost per 90 minutes."""
        return _per_90(self.possession_lost, self.minutes)

    @property
    def pressures_attempted_per_90(self) -> float | None:
        """Pressures attempted per 90 minutes."""
        return _per_90(self.pressures_attempted, self.minutes)

    @property
    def pressures_completed_per_90(self) -> float | None:
        """Pressures completed per 90 minutes."""
        return _per_90(self.pressures_completed, self.minutes)

    @property
    def blocks_per_90(self) -> float | None:
        """Blocks per 90 minutes."""
        return _per_90(self.blocks, self.minutes)

    @property
    def shots_blocked_per_90(self) -> float | None:
        """Shots blocked per 90 minutes."""
        return _per_90(self.shots_blocked, self.minutes)

    @property
    def clearances_per_90(self) -> float | None:
        """Clearances per 90 minutes."""
        return _per_90(self.clearances, self.minutes)

    @property
    def goals_allowed_per_90(self) -> float | None:
        """Goals allowed per 90 minutes."""
        return _per_90(self.goals_allowed, self.minutes)


register_field_statuses(
    PlayerSeasonStats,
    verified=(
        "player_uid",
        "player_name",
        "kind",
        "team_id",
        "club_uid",
        "club_name",
        "club_short_name",
        "starts",
        "substitute_appearances",
        "minutes",
        "rated_appearances",
        "average_rating",
        "goals",
        "assists",
        "expected_goals",
        "expected_assists",
        "shots",
        "shots_on_target",
        "shots_outside_box",
        "passes_attempted",
        "passes_completed",
        "progressive_passes",
        "key_passes",
        "open_play_key_passes",
        "clear_cut_chances_created",
        "crosses_attempted",
        "crosses_completed",
        "dribbles",
        "offsides",
        "distance_km",
        "high_intensity_sprints",
        "aerial_challenges_attempted",
        "headers_won",
        "tackles_attempted",
        "tackles_completed",
        "interceptions",
        "possession_won",
        "pressures_attempted",
        "pressures_completed",
        "clearances",
        "fouls_made",
        "fouls_against",
        "yellow_cards",
        "pass_completion_percent",
        "cross_completion_percent",
        "headers_won_percent",
        "tackle_completion_percent",
        "shots_on_target_percent",
        "goals_per_90",
        "assists_per_90",
        "expected_goals_per_90",
        "expected_assists_per_90",
        "shots_per_90",
        "shots_on_target_per_90",
        "shots_outside_box_per_90",
        "passes_attempted_per_90",
        "passes_completed_per_90",
        "progressive_passes_per_90",
        "key_passes_per_90",
        "open_play_key_passes_per_90",
        "clear_cut_chances_created_per_90",
        "crosses_attempted_per_90",
        "crosses_completed_per_90",
        "dribbles_per_90",
        "distance_km_per_90",
        "high_intensity_sprints_per_90",
        "aerial_challenges_attempted_per_90",
        "headers_won_per_90",
        "tackles_completed_per_90",
        "interceptions_per_90",
        "possession_won_per_90",
        "pressures_attempted_per_90",
        "pressures_completed_per_90",
        "clearances_per_90",
    ),
    unconfirmed=(
        "team_slot",
        "player_of_the_match",
        "goals_outside_box",
        "free_kick_shots",
        "penalties_taken",
        "penalties_scored",
        "open_play_crosses_attempted",
        "open_play_crosses_completed",
        "key_headers",
        "key_tackles",
        "blocks",
        "shots_blocked",
        "red_cards",
        "mistakes_leading_to_goal",
        "clean_sheets",
        "goals_allowed",
        "saves_held",
        "saves_parried",
        "saves_tipped",
        "shots_on_target_faced",
        "expected_goals_prevented",
        "non_penalty_expected_goals",
        "possession_lost",
        "open_play_cross_completion_percent",
        "conversion_percent",
        "save_percent",
        "expected_goals_per_shot",
        "expected_goals_prevented_per_90",
        "non_penalty_expected_goals_per_90",
        "possession_lost_per_90",
        "open_play_crosses_attempted_per_90",
        "open_play_crosses_completed_per_90",
        "headers_lost_per_90",
        "key_headers_per_90",
        "key_tackles_per_90",
        "blocks_per_90",
        "shots_blocked_per_90",
        "goals_allowed_per_90",
    ),
)
