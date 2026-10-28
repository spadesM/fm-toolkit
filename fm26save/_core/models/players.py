"""Player records: identity, ability, reputation, club, positions, attributes and traits.

Person fields (name, birth date, nationality, home-grown ids, personality and traits) come
from each player's person block; they stay None or empty when no block validates. Adjusted
and raw attributes share one coverage row per attribute, so one Attributes class serves both
`attributes` (the 1 to 20 display scale) and `raw_attributes` (the 1 to 100 raw scale).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import IntEnum

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue, TransferValueState
from fm26save._core.models.contracts import Contract
from fm26save._core.models.suspensions import PlayerSuspension


@dataclass(frozen=True, slots=True)
class Ability:
    """A player's current and potential ability.

    Attributes:
        current: Current ability (unconfirmed).
        potential: Potential ability, or None when the save stores a range code instead
            (unconfirmed).
        potential_range_code: The stored negative code when potential is unknown, else None
            (unconfirmed).
    """

    current: int
    potential: int | None
    potential_range_code: int | None


@dataclass(frozen=True, slots=True)
class Reputation:
    """A player's reputation figures.

    Never threshold on bucket: it is a coarse, lossy bucket that mis-orders players. Use
    current to rank players instead.

    Attributes:
        bucket: Coarse reputation bucket that loses precision (unconfirmed).
        home: Home reputation.
        current: Current reputation.
        world: World reputation.
    """

    bucket: int
    home: int
    current: int
    world: int


@dataclass(frozen=True, slots=True)
class Attributes:
    """52 non-foot player attributes, shared by the display and raw scales.

    Attributes:
        crossing: Crossing.
        dribbling: Dribbling.
        finishing: Finishing.
        heading: Heading.
        long_shots: Long shots.
        marking: Marking.
        off_the_ball: Off the ball movement.
        passing: Passing.
        penalty_taking: Penalty taking.
        tackling: Tackling.
        vision: Vision.
        handling: Goalkeeping handling.
        aerial_reach: Goalkeeping aerial reach.
        command_of_area: Goalkeeping command of area.
        communication: Goalkeeping communication.
        kicking: Goalkeeping kicking.
        throwing: Goalkeeping throwing.
        anticipation: Anticipation.
        decisions: Decisions.
        one_on_ones: Goalkeeping one-on-ones.
        positioning: Positioning (an attribute, not a position rating).
        reflexes: Goalkeeping reflexes.
        first_touch: First touch.
        technique: Technique.
        flair: Flair.
        corners: Corners.
        teamwork: Teamwork.
        work_rate: Work rate.
        long_throws: Long throws.
        eccentricity: Goalkeeping eccentricity.
        rushing_out: Goalkeeping tendency to rush out.
        punching: Goalkeeping tendency to punch crosses.
        acceleration: Acceleration.
        free_kick_taking: Free kick taking.
        strength: Strength.
        stamina: Stamina.
        pace: Pace.
        jumping_reach: Jumping reach.
        leadership: Leadership.
        dirtiness: Dirtiness, a hidden attribute.
        balance: Balance.
        bravery: Bravery.
        consistency: Consistency, a hidden attribute.
        aggression: Aggression.
        agility: Agility.
        important_matches: Big-match temperament, a hidden attribute.
        injury_proneness: Injury proneness, a hidden attribute.
        versatility: Versatility, a hidden attribute.
        natural_fitness: Natural fitness.
        determination: Determination.
        composure: Composure.
        concentration: Concentration.
    """

    crossing: int
    dribbling: int
    finishing: int
    heading: int
    long_shots: int
    marking: int
    off_the_ball: int
    passing: int
    penalty_taking: int
    tackling: int
    vision: int
    handling: int
    aerial_reach: int
    command_of_area: int
    communication: int
    kicking: int
    throwing: int
    anticipation: int
    decisions: int
    one_on_ones: int
    positioning: int
    reflexes: int
    first_touch: int
    technique: int
    flair: int
    corners: int
    teamwork: int
    work_rate: int
    long_throws: int
    eccentricity: int
    rushing_out: int
    punching: int
    acceleration: int
    free_kick_taking: int
    strength: int
    stamina: int
    pace: int
    jumping_reach: int
    leadership: int
    dirtiness: int
    balance: int
    bravery: int
    consistency: int
    aggression: int
    agility: int
    important_matches: int
    injury_proneness: int
    versatility: int
    natural_fitness: int
    determination: int
    composure: int
    concentration: int


@dataclass(frozen=True, slots=True)
class Positions:
    """The 15 position ratings, in the player rating array order.

    This is not the tactic or per-match position mask order.

    Attributes:
        gk: Goalkeeper.
        sw: Sweeper.
        dl: Left back.
        dc: Centre back.
        dr: Right back.
        dm: Defensive midfielder.
        ml: Left midfielder.
        mc: Central midfielder.
        mr: Right midfielder.
        aml: Attacking midfielder, left.
        amc: Attacking midfielder, centre.
        amr: Attacking midfielder, right.
        stc: Striker.
        wbl: Left wing back.
        wbr: Right wing back.
    """

    gk: int
    sw: int
    dl: int
    dc: int
    dr: int
    dm: int
    ml: int
    mc: int
    mr: int
    aml: int
    amc: int
    amr: int
    stc: int
    wbl: int
    wbr: int


@dataclass(frozen=True, slots=True)
class Personality:
    """A player's personality profile.

    Attributes:
        adaptability: Adaptability.
        ambition: Ambition.
        loyalty: Loyalty.
        pressure: Pressure.
        professionalism: Professionalism.
        sportsmanship: Sportsmanship.
        temperament: Temperament.
        controversy: Controversy.
    """

    adaptability: int
    ambition: int
    loyalty: int
    pressure: int
    professionalism: int
    sportsmanship: int
    temperament: int
    controversy: int


class Trait(IntEnum):
    """A named player trait; UNKNOWN keeps the bit number in CodedValue.raw.

    A bit is named only where a trait the game itself displayed pins that exact bit. Two
    readings do that. Six bits come from player profiles, which list a player's traits in
    ascending bit order, and that order is what ties a displayed trait to a bit. The other
    ten come from in-game trait panels read on 2026-09-16, one player per bit, each player's
    bitmask holding exactly one bit no earlier reading had reached, so the one unaccounted
    trait his panel showed is that bit.

    A name an outside name table would supply is not evidence for one, so every bit no
    displayed trait reaches is UNKNOWN and keeps its bit number. Neither is a name that
    merely looks likely from the bits around it, even though two such guesses were later
    borne out by a panel: what named those bits is the panel, not the guess.
    """

    UNKNOWN = -1
    RUNS_WITH_BALL_DOWN_LEFT = 0
    RUNS_WITH_BALL_DOWN_RIGHT = 1
    RUNS_WITH_BALL_THROUGH_CENTRE = 2
    MOVES_INTO_CHANNELS = 4
    GETS_FORWARD_WHENEVER_POSSIBLE = 5
    TRIES_KILLER_BALLS_OFTEN = 7
    SHOOTS_FROM_DISTANCE = 8
    LIKES_TO_TRY_TO_BEAT_OFFSIDE_TRAP = 13
    COMES_DEEP_TO_GET_BALL = 19
    DICTATES_TEMPO = 22
    KNOCKS_BALL_PAST_OPPONENT = 27
    AVOIDS_USING_WEAKER_FOOT = 34
    DIVES_INTO_TACKLES = 37
    TRIES_LONG_RANGE_PASSES = 43
    RUNS_WITH_BALL_OFTEN = 51
    CROSSES_EARLY = 59


@dataclass(frozen=True, slots=True)
class Player:
    """A player record from the save's game database.

    Person fields (name, birth date, nationality, home-grown ids, personality and traits)
    come from the player's person block; they stay None or empty when no block validates.

    Attributes:
        uid: The id fmsave reads for the player's record and joins every table on. It is not
            the game's Unique ID (that is unique_id): it is the Unique ID of the person stored
            just before him, so it differs between new games started from the same database
            (unconfirmed).
        unique_id: The player's Unique ID in the game database, the same in every new game
            started from that database. The game can give the id of a person it has deleted
            to one it creates later. None when the save's bytes cannot tell it (unconfirmed).
        name: Display name: common name first, else first plus last name, else legal name
            (unconfirmed).
        first_name: First name (unconfirmed).
        last_name: Last name (unconfirmed).
        common_name: Common (nickname) name, when the save stores one (unconfirmed).
        full_name: First name plus last name, or None when either is missing (unconfirmed).
        legal_name: The save's stored legal name, or None when the save stores none
            (unconfirmed).
        birth_date: Date of birth (unconfirmed).
        age: Age at the save's in-game clock date, or None when birth_date or the clock
            date is unreadable (unconfirmed).
        nation_id: Id of the player's primary nation (unconfirmed).
        second_nation_ids: Ids of the player's other eligible nations.
        home_grown_nation_ids: Ids of nations the player is considered home grown for.
        home_grown_club_uids: Uids of clubs the player is considered home grown for, in
            relation-list order; an entry is None when its club index does not resolve, but
            still keeps its position. They are Club.uid values and carry its status
            (unconfirmed).
        home_grown_club_names: Denormalised names for home_grown_club_uids, in the same
            order; None wherever home_grown_club_uids is None (unconfirmed).
        height_cm: Height in centimetres (unconfirmed).
        ability: Current and potential ability.
        reputation: Reputation figures; never threshold on reputation.bucket.
        club_uid: Uid of the club the player belongs to: the club fielding his registered
            team, which for a team an affiliate club stores is the club controlling it.
            None for a free agent or an unresolved team (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        club_short_name: Denormalised short name of club_uid (unconfirmed).
        club_nation_id: Denormalised league nation id of club_uid (unconfirmed).
        club_fa_nation_id: Denormalised FA nation id of club_uid (unconfirmed).
        club_reputation: Denormalised reputation of club_uid.
        club_last_league_position: Denormalised last completed season league position of
            club_uid.
        team_id: Id of the player's registered team, or None for a free agent
            (unconfirmed).
        team_slot: The team's slot in club_uid's team list, which counts that club's own
            slots first and then the teams it controls at affiliate clubs; None when
            team_id does not resolve to a club (unconfirmed).
        team_club_uid: Uid of the club whose record stores the player's registered team,
            when another club controls that team, else None (unconfirmed).
        team_club_name: Denormalised full name of team_club_uid; None wherever
            team_club_uid is (unconfirmed).
        club_join_date: Date the player joined his current club; it disagrees with the
            contract start date for about half of players, so it is not a substitute for it
            (unconfirmed).
        natural_positions: Position codes rated at least 18, best first.
        accomplished_positions: Position codes rated 15 to 17, best first. This is an
            fmsave classifier label, not text the game itself shows.
        personality: Personality profile, or None when no person block validates.
        attributes: The 52 non-foot attributes, on the 1 to 20 display scale.
        raw_attributes: The same 52 attributes, on the 1 to 100 raw scale.
        left_foot: Left foot strength, on the 1 to 20 display scale.
        right_foot: Right foot strength, on the 1 to 20 display scale.
        raw_left_foot: Left foot strength, on the 1 to 100 raw scale.
        raw_right_foot: Right foot strength, on the 1 to 100 raw scale.
        positions: The 15 position ratings.
        transfer_value: Transfer value in the save's base currency, set only when
            transfer_value_state is OK.
        transfer_value_state: How transfer_value was read from the save (unconfirmed).
        raw_condition: Condition, on the 0 to 10000 scale the save stores it on. The
            game shows condition as a percentage, which is this divided by 100.
        raw_match_sharpness: Match sharpness, on the 0 to 10000 scale the save stores
            it on. The game shows it as a percentage, which is this divided by 100.
        traits: Named player traits; an unnamed bit is Trait.UNKNOWN with raw set to the
            bit number.
        trait_bits: The raw trait bitmask, or None when no person block validates.
        on_loan: Whether the player is on loan from the club of his contract in effect:
            True when he is registered with another club's team and the save holds a loan
            for him there that has not ended, False when it does not, and None when his
            club or his contract in effect is unknown. A player registered with a team his
            own club controls, such as a B team, is a player of that club, not on loan.
        loan_parent_club_uid: Uid of the club of the contract in effect when on_loan is
            True, else None. It is the contract's club_uid under another name, so it carries
            the same status (unconfirmed).
        loan_parent_club_name: Denormalised name of loan_parent_club_uid (unconfirmed).
        loan_start: Date the loan began when on_loan is True, else None. It is also None
            when the loan's stored start does not decode as a game date, which keeps an
            unreadable start from costing the player his loan; no save read so far holds
            such a loan.
        loan_end: Date the loan ends when on_loan is True, else None.
        contract: The player's current contract, or None when a current contract cannot be
            established.
        suspensions: The player's unserved suspensions, in the order the save stores them,
            including bans the game no longer displays; () when the player has none.
    """

    uid: int
    unique_id: int | None
    name: str | None
    first_name: str | None
    last_name: str | None
    common_name: str | None
    full_name: str | None
    legal_name: str | None
    birth_date: date | None
    age: int | None
    nation_id: int | None
    second_nation_ids: tuple[int, ...]
    home_grown_nation_ids: tuple[int, ...]
    home_grown_club_uids: tuple[int | None, ...]
    home_grown_club_names: tuple[str | None, ...]
    height_cm: int
    ability: Ability
    reputation: Reputation
    club_uid: int | None
    club_name: str | None
    club_short_name: str | None
    club_nation_id: int | None
    club_fa_nation_id: int | None
    club_reputation: int | None
    club_last_league_position: int | None
    team_id: int | None
    team_slot: int | None
    team_club_uid: int | None
    team_club_name: str | None
    club_join_date: date | None
    natural_positions: tuple[str, ...]
    accomplished_positions: tuple[str, ...]
    personality: Personality | None
    attributes: Attributes
    raw_attributes: Attributes
    left_foot: int
    right_foot: int
    raw_left_foot: int
    raw_right_foot: int
    positions: Positions
    transfer_value: int | None
    transfer_value_state: TransferValueState
    raw_condition: int
    raw_match_sharpness: int
    traits: tuple[CodedValue[Trait], ...]
    trait_bits: int | None
    on_loan: bool | None
    loan_parent_club_uid: int | None
    loan_parent_club_name: str | None
    loan_start: date | None
    loan_end: date | None
    contract: Contract | None
    suspensions: tuple[PlayerSuspension, ...]


register_field_statuses(Ability, unconfirmed=("current", "potential", "potential_range_code"))
register_field_statuses(Reputation, verified=("home", "current", "world"), unconfirmed=("bucket",))
register_field_statuses(
    Attributes,
    verified=(
        "crossing",
        "dribbling",
        "finishing",
        "heading",
        "long_shots",
        "marking",
        "off_the_ball",
        "passing",
        "penalty_taking",
        "tackling",
        "vision",
        "handling",
        "aerial_reach",
        "command_of_area",
        "communication",
        "kicking",
        "throwing",
        "anticipation",
        "decisions",
        "one_on_ones",
        "positioning",
        "reflexes",
        "first_touch",
        "technique",
        "flair",
        "corners",
        "teamwork",
        "work_rate",
        "long_throws",
        "eccentricity",
        "rushing_out",
        "punching",
        "acceleration",
        "free_kick_taking",
        "strength",
        "stamina",
        "pace",
        "jumping_reach",
        "leadership",
        "dirtiness",
        "balance",
        "bravery",
        "consistency",
        "aggression",
        "agility",
        "important_matches",
        "injury_proneness",
        "versatility",
        "natural_fitness",
        "determination",
        "composure",
        "concentration",
    ),
)
register_field_statuses(
    Positions,
    verified=(
        "gk",
        "sw",
        "dl",
        "dc",
        "dr",
        "dm",
        "ml",
        "mc",
        "mr",
        "aml",
        "amc",
        "amr",
        "stc",
        "wbl",
        "wbr",
    ),
)
register_field_statuses(
    Personality,
    verified=(
        "adaptability",
        "ambition",
        "loyalty",
        "pressure",
        "professionalism",
        "sportsmanship",
        "temperament",
        "controversy",
    ),
)
# A field taken from another record carries that record's status: the home-grown club uids and
# names are Club.uid and Club.name, and the loan parent club is the contract's club.
register_field_statuses(
    Player,
    verified=(
        "second_nation_ids",
        "home_grown_nation_ids",
        "club_reputation",
        "club_last_league_position",
        "natural_positions",
        "accomplished_positions",
        "left_foot",
        "right_foot",
        "raw_left_foot",
        "raw_right_foot",
        "transfer_value",
        "raw_condition",
        "raw_match_sharpness",
        "traits",
        "trait_bits",
        "on_loan",
        "loan_start",
        "loan_end",
        "suspensions",
    ),
    unconfirmed=(
        "uid",
        "unique_id",
        "name",
        "first_name",
        "last_name",
        "common_name",
        "full_name",
        "legal_name",
        "birth_date",
        "age",
        "nation_id",
        "height_cm",
        "club_uid",
        "club_name",
        "club_short_name",
        "club_nation_id",
        "club_fa_nation_id",
        "team_id",
        "team_slot",
        "team_club_uid",
        "team_club_name",
        "club_join_date",
        "transfer_value_state",
        "home_grown_club_uids",
        "home_grown_club_names",
        "loan_parent_club_uid",
        "loan_parent_club_name",
    ),
)
