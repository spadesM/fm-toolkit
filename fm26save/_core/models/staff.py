"""The people a club employs who are not players, and the lists a club keeps them in.

A row is one person at one club: the department list the club keeps him in, the terms of his
contract, his ability, and the preferences a staff profile shows. The human manager is a row of
his own with no readable ability.

**The club's board is not here.** A club's staff screen shows its president, its director and
its managing director beside the coaching and medical staff, and none of the three has a row in
the staff structures this reads; the rest of that screen's people matched a row one for one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.players import Ability, Personality


@dataclass(frozen=True, slots=True)
class StaffPreferences:
    """How a member of staff prefers a team to be run, each on a 1 to 20 scale.

    These are preferences, not rated attributes: a high `directness` says what the person wants
    from a side, never how good he is at anything. Fourteen of the save's twenty-six slots have
    a name; the rest ship as `Staff.unknown["preference_slot_<i>"]`.

    Attributes:
        attacking: How attacking a side he wants.
        business: How commercial he wants the club to be.
        directness: How direct he wants the passing.
        interference: How much he involves himself in other people's work.
        patience: How patient he is with a plan.
        trigger_press: How eagerly he wants the side to press.
        resources: How freely he wants the club's resources spent.
        buying_players: How readily he wants players bought.
        mind_games: How much he plays on an opponent's mind.
        flexibility: How willing he is to change an approach.
        hardness_of_training: How hard he wants the side trained.
        squad_rotation: How much he wants the side rotated.
        tempo: How quickly he wants the side to play.
        width: How wide he wants the side to play.
    """

    attacking: int
    business: int
    directness: int
    interference: int
    patience: int
    trigger_press: int
    resources: int
    buying_players: int
    mind_games: int
    flexibility: int
    hardness_of_training: int
    squad_rotation: int
    tempo: int
    width: int


@dataclass(frozen=True, slots=True)
class StaffAttributes:
    """The one rated staff attribute located in the save.

    A staff profile rates about twenty attributes; only this one has been found, and it is the
    same byte as `Staff.personality.adaptability`, so the two always agree.

    Attributes:
        adaptability: Adaptability, on the same 1 to 20 scale a player's is.
    """

    adaptability: int


@dataclass(frozen=True, slots=True)
class Staff:
    """One member of staff at one club.

    A person listed by a club's affiliate side and paid by the club itself is **one row at the
    club**, with the side that lists him in `listed_club_uid`, the same rule a player on a B
    team follows. A person a club lists but pays nothing has no contract to read, so `wage`,
    `contract_start` and `contract_end` are None rather than zero.

    `unknown["contract_e36"]` and the three codes beside it are **not** player squad statuses:
    they come from the same bytes but take different values on staff, and no displayed label has
    named one, so they ship as raw numbers and never as a `SquadStatus`.

    **The job title is not readable, and `unknown["r4"]` is not it.** That byte was the one
    candidate for it, and a club's staff screen ruled it out: over 78 displayed rows, 8 of the
    16 codes on show carried two or more different job titles, 7 titles appeared under two or
    three different codes, and one code carried seven titles on its own. So `r4` keeps its raw
    number for good rather than becoming a named role, and the codes that happen to sit on one
    title at one club are not evidence of a meaning the field demonstrably does not have.

    The human manager is a row with `is_human_manager` true. His object is laid out differently,
    so `ability`, `preferences` and every `unknown` key read from the ability block are absent
    for him, while his name, birth date, personality and contract read normally.

    Attributes:
        uid: The id fmsave reads for the person's object and joins every table on. It is not
            the game's Unique ID (that is unique_id): it is the Unique ID of the person stored
            just before him, so it differs between new games started from the same database
            (unconfirmed).
        unique_id: The person's Unique ID in the game database, the same in every new game
            started from that database. The game can give the id of a person it has deleted
            to one it creates later. None when the save's bytes cannot tell it (unconfirmed).
        is_human_manager: Whether this is the save's own human manager (unconfirmed).
        name: Common name, else first and last name, else legal name (unconfirmed).
        first_name: First name (unconfirmed).
        last_name: Surname (unconfirmed).
        common_name: The name the game shows in place of the full name (unconfirmed).
        full_name: First and last name together, when both are known (unconfirmed).
        legal_name: The stored legal name (unconfirmed).
        birth_date: Date of birth (unconfirmed).
        age: Age at the save's in-game date (unconfirmed).
        nation_id: Nation id (unconfirmed).
        club_uid: Uid of the club the person works for.
        club_name: Denormalised full name of club_uid.
        team_id: The team his contract registers him with, None without a contract.
        team_slot: That team's slot in the club's team list, None without a contract
            (unconfirmed).
        listed_club_uid: The club whose own staff list holds him, which is club_uid unless an
            affiliate side lists him; None when no list holds him (unconfirmed).
        listed_club_name: Denormalised full name of listed_club_uid; None wherever
            listed_club_uid is (unconfirmed).
        in_club_lists: Whether a club's staff list holds him at all (unconfirmed).
        list_indexes: Which of the three lists hold him, 0 to 2, empty when none does
            (unconfirmed).
        has_contract: Whether a contract at club_uid was read for him (unconfirmed).
        wage: What the contract pays, per week, in the save's base currency; None without a
            contract.
        contract_start: The day the contract started.
        contract_end: The day it ends, None when the save stores none (unconfirmed).
        ability: Current and potential ability, None when the object carries no readable
            ability block, as the human manager's does not.
        personality: The eight personality values, None without a name block.
        attributes: The one rated attribute located, None without a name block.
        preferences: The named preferences, None when the object carries no readable ability
            block.
        unknown: Numeric fields with no known meaning (unconfirmed). The ability-block keys
            (`entry_count`, `r4` to `r12` and every `preference_slot_*`) are absent when that
            block does not read, and the `contract_*` keys when no contract was read.
    """

    uid: int
    unique_id: int | None
    is_human_manager: bool
    name: str | None
    first_name: str | None
    last_name: str | None
    common_name: str | None
    full_name: str | None
    legal_name: str | None
    birth_date: date | None
    age: int | None
    nation_id: int | None
    club_uid: int
    club_name: str
    team_id: int | None
    team_slot: int | None
    listed_club_uid: int | None
    listed_club_name: str | None
    in_club_lists: bool
    list_indexes: tuple[int, ...]
    has_contract: bool
    wage: int | None
    contract_start: date | None
    contract_end: date | None
    ability: Ability | None
    personality: Personality | None
    attributes: StaffAttributes | None
    preferences: StaffPreferences | None
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = (
        "entry_count",
        "r4",
        "r5",
        "r6",
        "r7",
        "r8",
        "r9",
        "r10",
        "r11",
        "r12",
        "preference_slot_2",
        "preference_slot_4",
        "preference_slot_5",
        "preference_slot_7",
        "preference_slot_8",
        "preference_slot_12",
        "preference_slot_13",
        "preference_slot_16",
        "preference_slot_17",
        "preference_slot_18",
        "preference_slot_19",
        "preference_slot_20",
        *(f"b40_raw_{i}" for i in range(26)),
        *(f"b40_20_{i}" for i in range(26)),
        "contract_e36",
        "contract_e37",
        "contract_e38",
        "contract_e39",
        "contract_type",
    )


@dataclass(frozen=True, slots=True)
class StaffList:
    """One of the three staff lists a club record holds, for one club.

    A club that lists nobody has no row here at all; a club that lists somebody has all three
    rows, empty lists included. The lists split a club's staff into groups, and the codes their
    members carry differ from list to list.

    **The three lists look like the three departments a club's staff screen shows.** On one
    club, the screen's medical, coaching and recruitment panels and the club's senior rows in
    lists 0, 1 and 2 held the same people, person for person by name, save for the human
    manager and one contracted person no list holds; that makes list 0 medical, list 1
    coaching and list 2 recruitment. It is arithmetic on one club rather than a label on a
    list, so it is recorded here and `list_index` stays a number.

    People a list holds who turn out to be players are dropped, and so are the few whose object
    cannot be told from another's, so a list's people are those `staff()` also has a row for.

    Attributes:
        club_uid: Uid of the club whose record holds the list (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        list_index: Which of the club's three lists this is, 0 to 2 (unconfirmed).
        staff_uids: The uid of each person the list holds, in stored order. They are
            `Staff.uid` values and join to the staff table (unconfirmed).
        staff_names: Each of those people's name, aligned with staff_uids
            (unconfirmed).
    """

    club_uid: int
    club_name: str
    list_index: int
    staff_uids: tuple[int, ...]
    staff_names: tuple[str | None, ...]


register_field_statuses(
    StaffPreferences,
    verified=(
        "attacking",
        "business",
        "directness",
        "interference",
        "patience",
        "trigger_press",
        "resources",
        "buying_players",
        "mind_games",
        "flexibility",
        "hardness_of_training",
        "squad_rotation",
        "tempo",
        "width",
    ),
)
register_field_statuses(StaffAttributes, verified=("adaptability",))
register_field_statuses(
    Staff,
    verified=("club_uid", "club_name", "team_id", "wage", "contract_start"),
    unconfirmed=(
        "uid",
        "unique_id",
        "is_human_manager",
        "name",
        "first_name",
        "last_name",
        "common_name",
        "full_name",
        "legal_name",
        "birth_date",
        "age",
        "nation_id",
        "team_slot",
        "listed_club_uid",
        "listed_club_name",
        "in_club_lists",
        "list_indexes",
        "has_contract",
        "contract_end",
        "unknown",
    ),
)
register_field_statuses(
    StaffList,
    unconfirmed=("club_uid", "club_name", "list_index", "staff_uids", "staff_names"),
)
