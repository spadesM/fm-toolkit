"""The corporate facilities rating a club's own record carries.

One row per club that keeps a monthly finance series, which is the clubs of the one or two
league nations a save tracks rather than every club it holds. The value is the rating the
game's Facilities screen shows as a word on its Corporate line, and the save keeps it as a
small number with no text beside it.

**Seventeen of the twenty codes have a word.** Fifteen were read off a club's own Facilities
screen, one club per code, and the words rise with the number: several numbers share a word,
which is what a rating shown as a word rather than a number looks like. Two more are named
because they are bracketed, not because a pattern was extrapolated. The three codes no club in
the save carried are `UNKNOWN` and keep their raw number: a word nobody has seen displayed is
silently wrong where a raw number is plainly incomplete.

The screen's other facility lines -- the stadium, the pitch, the training and youth grounds,
the academy -- have no candidate byte anywhere near this one, so nothing here reads them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType

from fm26save._core._status import register_field_statuses
from fm26save._core.models.common import CodedValue


class CorporateFacilities(IntEnum):
    """How good a club's corporate facilities are, in the game's own words.

    A member's value is the lowest code its word was displayed against; every code the word
    covers reads as that member and keeps its own raw number.

    **Fifteen codes are named by a screen.** One club's Facilities screen per code displayed
    that word against that exact stored number: 1 and 2 Basic, 5 Fairly Basic, 6, 7 and 9
    Adequate, 10, 11 and 12 Average, 13 and 15 Good, and 17, 18, 19 and 20 Excellent.

    **Two more are named by bracketing, which is not band inference.** Code 8 sits between 7
    and 9, both displayed Adequate, and code 14 between 13 and 15, both displayed Good, so on
    a scale whose words rise with the number each of those can only be the word its
    neighbours carry. Nothing else is filled in that way.

    **Codes 3, 4 and 16 are UNKNOWN**, because no club in the save carries them: 3 and 4 are
    below the lowest Fairly Basic seen and 16 sits between a Good and an Excellent, so neither
    a screen nor a bracket names them. The reading that the words sit in fixed bands of the
    scale would name them, and it is a hypothesis rather than an observation, so it is not
    shipped.
    """

    UNKNOWN = -1
    BASIC = 1
    FAIRLY_BASIC = 5
    ADEQUATE = 6
    AVERAGE = 10
    GOOD = 13
    EXCELLENT = 17

    @classmethod
    def _missing_(cls, value: object) -> CorporateFacilities | None:
        """The further codes each word covers, and no other code."""
        return _FURTHER_CODES.get(value) if isinstance(value, int) else None


# Every code above a word's own member value that the same word covers: those a screen
# displayed that word against, and the two the clubs either side of them bracket.
_FURTHER_CODES: Mapping[int, CorporateFacilities] = MappingProxyType(
    {
        2: CorporateFacilities.BASIC,
        7: CorporateFacilities.ADEQUATE,
        8: CorporateFacilities.ADEQUATE,
        9: CorporateFacilities.ADEQUATE,
        11: CorporateFacilities.AVERAGE,
        12: CorporateFacilities.AVERAGE,
        14: CorporateFacilities.GOOD,
        15: CorporateFacilities.GOOD,
        18: CorporateFacilities.EXCELLENT,
        19: CorporateFacilities.EXCELLENT,
        20: CorporateFacilities.EXCELLENT,
    }
)


@dataclass(frozen=True, slots=True)
class ClubFacilities:
    """One club's facility ratings, as its own record stores them.

    Attributes:
        club_uid: Uid of the club (unconfirmed).
        club_name: Denormalised full name of club_uid (unconfirmed).
        corporate_facilities: How good the club's corporate facilities are. Seventeen of the
            twenty codes carry a word, and the three no club in the save carries are UNKNOWN
            with the raw number kept. A club that stores no rating reads UNKNOWN with raw 0.
    """

    club_uid: int
    club_name: str
    corporate_facilities: CodedValue[CorporateFacilities]


# The rating is read from a fixed offset past the end of the club's own finance chain, and a
# club's screen named what the field is, so the field is verified even where a label is not.
# The club key and its name are the finance reader's, and carry that reader's status.
register_field_statuses(
    ClubFacilities,
    verified=("corporate_facilities",),
    unconfirmed=("club_uid", "club_name"),
)
