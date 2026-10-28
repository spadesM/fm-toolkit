"""The manager's tactics and set-piece routines, as the save stores them per team.

**A tactic belongs to a team, not to a club.** The save keeps a separate copy of each tactic
for each team that uses it, so a manager with two tactics and two teams using them has four
records, and the copies are not byte-identical. A row here is one stored copy, keyed on the
team and the tactic's place in that team's own list, and the same tactic name appears once per
team.

**The mentality is named; almost nothing else here is.** The seven mentality codes carry the
seven words the game shows, read off a manager's own tactics. The position bits, the 19 team
instruction bytes and the 24-byte setting units are read from offsets that are pinned by
measurement, but no displayed label has been matched to one of those codes, so every one of
their labels is `UNKNOWN` and every unnamed number ships raw. The position bits do agree with
the natural positions of the players picked in each slot, which is a corroboration against
another decoded field rather than a displayed formation, so it names no bit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


class Mentality(IntEnum):
    """How attacking a tactic's mentality is, in the game's own words.

    The seven codes are the seven mentalities the game offers, in the order it lists them, and
    the manager of the save they were read from confirmed the list against his own tactics: the
    tactic showing Attacking stores 6 and the two showing Balanced store 4. A code outside the
    seven is UNKNOWN and keeps its raw number.
    """

    UNKNOWN = -1
    VERY_DEFENSIVE = 1
    DEFENSIVE = 2
    CAUTIOUS = 3
    BALANCED = 4
    POSITIVE = 5
    ATTACKING = 6
    VERY_ATTACKING = 7


class TacticPosition(IntEnum):
    """One position of a tactic's formation.

    A member's value is the bit number set in a slot's position mask, counting from zero. Every
    code is UNKNOWN: no bit is named until a displayed formation pins it. This is deliberately
    **not** the same enum as `fmsave.models.matches.MatchPosition`, whose codes come from a
    different field and are ordinals rather than bit numbers.
    """

    UNKNOWN = -1


@dataclass(frozen=True, slots=True)
class TacticSettingUnit:
    """One 24-byte setting unit of a tactic slot, as two bit fields.

    A slot holds between none and about twenty of these, and they are what the player
    instructions of that position most likely are, but the save stores no name for either
    field, so both ship as the numbers they are. Every field is unconfirmed.

    Attributes:
        head_byte: The byte after the unit's lead bytes, which is 0 on most units and 2 or 10
            on the rest (unconfirmed).
        first_bits: The unit's seven-byte bit field as one little-endian int; between none and
            four of its bits are set (unconfirmed).
        second_bits_low: Bits 0 to 31 of the unit's twelve-byte bit field (unconfirmed).
        second_bits_middle: Bits 32 to 63 of that field (unconfirmed).
        second_bits_high: Bits 64 to 95 of that field. The field is wider than 64 bits, so it
            ships as three words rather than one int no column type could hold; one or two of
            its 96 bits are set, always above bit 32 (unconfirmed).
    """

    head_byte: int
    first_bits: int
    second_bits_low: int
    second_bits_middle: int
    second_bits_high: int


@dataclass(frozen=True, slots=True)
class TacticSlot:
    """One position of a tactic, in possession and out of possession.

    A tactic holds eleven of these in stored order. The mask is the field the positions come
    from: its low bits are positions and its two high bits flag which of a pair of central or
    wide slots is on which side, so the flags are in `*_mask` but never in `*_positions`.

    Attributes:
        number: The slot's place in the tactic, 0 for the first.
        in_possession_positions: The positions the in-possession mask sets, in ascending bit
            number; every label is UNKNOWN and the raw value is the bit number.
        in_possession_mask: The whole in-possession mask, column flags included.
        in_possession_setting_count: How many setting units the in-possession block holds
            (unconfirmed).
        in_possession_settings: Those units, in stored order (unconfirmed).
        out_of_possession_positions: The same for the out-of-possession block, which differs
            from the in-possession one on some slots of some saves.
        out_of_possession_mask: The whole out-of-possession mask.
        out_of_possession_setting_count: How many setting units that block holds
            (unconfirmed).
        out_of_possession_settings: Those units, in stored order (unconfirmed).
        unknown: The two bit fields each block carries besides its units, and the index byte
            the out-of-possession block carries. The role bits hold exactly one bit and are
            most likely the position's role, and the index bytes of a record are a permutation
            of 0 to 10 which is the identity on all but one record measured (unconfirmed).
    """

    number: int
    in_possession_positions: tuple[CodedValue[TacticPosition], ...]
    in_possession_mask: int
    in_possession_setting_count: int
    in_possession_settings: tuple[TacticSettingUnit, ...]
    out_of_possession_positions: tuple[CodedValue[TacticPosition], ...]
    out_of_possession_mask: int
    out_of_possession_setting_count: int
    out_of_possession_settings: tuple[TacticSettingUnit, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = (
        "in_possession_role_bits",
        "in_possession_trail_bits",
        "out_of_possession_role_bits",
        "out_of_possession_trail_bits",
        "out_of_possession_position_index",
    )


@dataclass(frozen=True, slots=True)
class Tactic:
    """One stored copy of one tactic, belonging to one team.

    Attributes:
        club_uid: Uid of the club the team plays for, None for a team no club lists
            (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        team_id: The team the copy belongs to, as the save stores it (unconfirmed).
        team_slot: The team's place in that club's own team list, 0 for its first team; None
            when the team resolves to no club (unconfirmed).
        index: The copy's place among the team's own tactics, counting from zero in stored
            order. Nothing stored says which of them is selected (unconfirmed).
        name: Stored tactic name (unconfirmed).
        style_name: The tactical style shown with the tactic, as stored text. No screen has
            confirmed that this label is the style (unconfirmed).
        mentality: The mentality the tactic is set to; the seven codes the game offers each
            carry the word it shows for them, and any other code reads UNKNOWN.
        slots: The eleven positions, in stored order.
        unknown: The 19 team-instruction bytes, one int per byte, and the tactic's four-byte
            style code as one little-endian int. Byte 2 of the instructions is the mentality
            and is shipped as `mentality` as well; bytes 0, 3, 4, 5, 7, 17 and 18 are the same
            on every record measured, and bytes 11 to 15 look bit-packed rather than numeric
            (unconfirmed).
    """

    club_uid: int | None
    club_name: str | None
    team_id: int
    team_slot: int | None
    index: int
    name: str
    style_name: str
    mentality: CodedValue[Mentality]
    slots: tuple[TacticSlot, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = tuple(
        f"team_instruction_{position:02d}" for position in range(19)
    ) + ("style_code",)


@dataclass(frozen=True, slots=True)
class SetPieceRoutine:
    """One set-piece routine slot of one team, named or unnamed.

    Attributes:
        club_uid: Uid of the club the team plays for, None for a team no club lists
            (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        team_id: The team the slot belongs to, as the save stores it (unconfirmed).
        team_slot: The team's place in that club's own team list, 0 for its first team; None
            when the team resolves to no club (unconfirmed).
        slot: The routine's place in the team's stored routines, counting from zero in stored
            order. Which set-piece situation a slot is for is not stored as text, so the slot
            number is all there is to go on (unconfirmed).
        name: Stored routine name, or None when unnamed. A team may store more than 20
            routines.
    """

    club_uid: int | None
    club_name: str | None
    team_id: int
    team_slot: int | None
    slot: int
    name: str | None


register_field_statuses(
    TacticSettingUnit,
    unconfirmed=(
        "head_byte",
        "first_bits",
        "second_bits_low",
        "second_bits_middle",
        "second_bits_high",
    ),
)
# The mask, the positions it sets and the slot's own number come from offsets a strict walk of
# every slot block on every save measured lands on exactly. What a setting unit is, and what
# the two bit fields beside the units mean, is not stored anywhere in the save.
register_field_statuses(
    TacticSlot,
    verified=(
        "number",
        "in_possession_positions",
        "in_possession_mask",
        "out_of_possession_positions",
        "out_of_possession_mask",
    ),
    unconfirmed=(
        "in_possession_setting_count",
        "in_possession_settings",
        "out_of_possession_setting_count",
        "out_of_possession_settings",
        "unknown",
    ),
)
# The mentality byte and the slots are read from a record the walk consumes exactly, and the
# mentality's own words come off a manager's tactics screen; the slots' position bits stay
# UNKNOWN, which is about the labels rather than the field. Everything else is either a join
# fmsave makes (the club and team fields), a number the save keeps with no name for it, or text
# no screen has confirmed the meaning of.
register_field_statuses(
    Tactic,
    verified=("mentality", "slots"),
    unconfirmed=(
        "club_uid",
        "club_name",
        "team_id",
        "team_slot",
        "index",
        "name",
        "style_name",
        "unknown",
    ),
)
register_field_statuses(
    SetPieceRoutine,
    verified=("name",),
    unconfirmed=("club_uid", "club_name", "team_id", "team_slot", "slot"),
)
