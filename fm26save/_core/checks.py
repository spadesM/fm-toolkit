"""The reader checks a save reports, and the validation report built from them.

While a reader decodes, it counts what it sees and compares those counts with the loose bounds
registered for the save's layout. A check that misses its bounds raises `GateCheckError` on a
save opened with `strict=True`, and otherwise warns `ReaderCheckWarning` with the same message
and lets the reader hand its table back: a bound is a measurement of the saves it was drawn
from and no more, so a save unlike those is not a save fmsave should refuse to read. A failure
carries its `ReaderCheck` records, so a caller reads the gate names, the observed values and
the bounds from fields rather than out of the message text.

`validate_save` runs every reader and returns a `ValidationReport`, which holds only structural
facts, counts and rates: never names, uids or other values from the save.

This module is the public face of the checks. How they are evaluated, which readers share a
decode and what each check measures are fmsave's to change, and live in `fmsave._checks`.
"""

from __future__ import annotations

from fm26save._core._checks import (
    GateCheckError,
    GateResult,
    ReaderCheck,
    ReaderStatus,
    ReaderValidation,
    ValidationReport,
    validate_save,
)

__all__ = [
    "GateCheckError",
    "GateResult",
    "ReaderCheck",
    "ReaderStatus",
    "ReaderValidation",
    "ValidationReport",
    "validate_save",
]
