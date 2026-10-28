"""Values shared by several record types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum

_UNKNOWN_MEMBER_NAME = "UNKNOWN"
_UNKNOWN_MEMBER_VALUE = -1


@dataclass(frozen=True, slots=True)
class CodedValue[EnumT: IntEnum]:
    """A number the save uses as a code, with its label.

    Codes without a verified meaning get the enum's UNKNOWN label and keep their raw number.
    Every coded enum has an UNKNOWN member with the value -1, which no stored code can equal.

    Attributes:
        label: The enum member for the code, or UNKNOWN.
        raw: The number exactly as stored in the save.
    """

    label: EnumT
    raw: int

    @classmethod
    def from_raw[LabelT: IntEnum](cls, enum_type: type[LabelT], raw: int) -> CodedValue[LabelT]:
        """Label a raw code from the save.

        Raises:
            TypeError: enum_type has no UNKNOWN member with the value -1.
        """
        unknown_label = enum_type.__members__.get(_UNKNOWN_MEMBER_NAME)
        if unknown_label is None or unknown_label.value != _UNKNOWN_MEMBER_VALUE:
            raise TypeError(
                f"{enum_type.__name__} needs an {_UNKNOWN_MEMBER_NAME} member "
                f"with the value {_UNKNOWN_MEMBER_VALUE}"
            )
        try:
            label = enum_type(raw)
        except ValueError:
            label = unknown_label
        return CodedValue(label=label, raw=raw)

    @property
    def label_text(self) -> str:
        """The label's member name in lowercase, for example "regular_starter"."""
        return self.label.name.lower()


class TransferValueState(StrEnum):
    """How a transfer value was read from the save."""

    OK = "ok"
    UNSET = "unset"
    PLACEHOLDER = "placeholder"
    ZERO = "zero"


class ContractEndSource(StrEnum):
    """Where a contract's end date was read from.

    CONTRACT is the contract record itself, which is where an end date belongs and where
    almost every one comes from. PLAYER_RECORD is the player's own record, which fmsave falls
    back to when no contract record of the player's gives up an end date. NONE is a contract
    whose end date neither source holds.
    """

    CONTRACT = "contract"
    PLAYER_RECORD = "player_record"
    NONE = "none"
