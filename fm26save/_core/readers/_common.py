"""Values and error-context helpers shared by the readers."""

from __future__ import annotations

import re
import struct
from collections.abc import Sequence

from fm26save._core._errors import ISSUES_URL, ReaderCheckError

# The value the save stores in a u32 id or index field that refers to nothing.
MISSING_REFERENCE = 0xFFFFFFFF

# The one section every game_db reader (names, clubs, players) works from.
GAME_DB_SECTION = "game_db"

# The unnamed run of frames between the `non_pl_hist_ls` and `humans` directory entries,
# which holds the fixture calendar, the league-table blocks and the rules preambles.
SPAN_REGION = "unlisted_after_non_pl_hist_ls"

# The per-match directory entries (`.apm` and `.scm`), which are not sections and hold the
# injury-type name table. They are one layout region, keyed by no schema number.
MATCH_FILE_REGION = "match_file"

# The small sections the managed-club reader works from, besides game_db.
HUMANS_SECTION = "humans"
SAVE_SUMMARY_SECTION = "save_game_summary"

# The open-vacancy feed the job centre screen lists, a few KB of fixed-size records.
JOB_CENTRE_SECTION = "job_centre"

# The groups of clubs the save stores together, a few KB of variable-length groups.
FEEDER_SECTION = "feeder_man"

# The injury history: a few megabytes of fixed-stride arrays, walked whole.
INJURY_MANAGER_SECTION = "injury_manager"

# The manager's tactics and set-piece routines, a few MB of which all but the first few KB is a
# store of line-ups for other clubs that fmsave never walks.
TACTICS_SECTION = "tactics_man"

# The training calendars, mentoring groups and saved schedules of the managed club's teams,
# tens of KB of variable-length blocks.
TRAINING_SECTION = "training_man"


def section_label(file_name: str, section_name: str = GAME_DB_SECTION) -> str:
    """ "<file name>: section '<section name>'", the common prefix of a reader's error text."""
    return f"{file_name}: section {section_name!r}"


def layout_mismatch(
    file_name: str, detail: str, section_name: str = GAME_DB_SECTION
) -> ReaderCheckError:
    """A ReaderCheckError saying the save layout differs from what fmsave expects."""
    return ReaderCheckError(
        f"{section_label(file_name, section_name)}: {detail}, so the save layout differs from "
        f"what fmsave expects. Please report it at {ISSUES_URL}"
    )


# How far to shift a year for its high byte. A stored year is a little-endian u16.
_YEAR_HIGH_BYTE_SHIFT = 8


def year_bytes_pattern(years: range) -> bytes:
    """A regex matching any of `years` stored as a little-endian u16.

    Each high byte the years reach gets its own low-byte class, so a window that crosses a
    high byte, such as 2047 to 2048, is covered whole. Every alternative is two bytes long.

    Raises:
        ValueError: The window holds no year.
    """
    if not years:
        raise ValueError(f"the year window {years.start} to {years.stop - 1} holds no year")
    alternatives: list[bytes] = []
    for high_byte in sorted({year >> _YEAR_HIGH_BYTE_SHIFT for year in years}):
        low_bytes = [year & 0xFF for year in years if year >> _YEAR_HIGH_BYTE_SHIFT == high_byte]
        alternatives.append(
            b"["
            + re.escape(bytes((low_bytes[0],)))
            + b"-"
            + re.escape(bytes((low_bytes[-1],)))
            + b"]"
            + re.escape(bytes((high_byte,)))
        )
    return b"(?:" + b"|".join(alternatives) + b")"


def build_gap_padded_struct(
    fields: Sequence[tuple[int, str, str]], *, start_offset: int | None = None
) -> tuple[struct.Struct, int, dict[str, int]]:
    """One little-endian struct spanning the given (offset, format_code, name) fields.

    Fields are sorted by offset; any gap between them (or before the first one) is padded
    with `x`. Returns (struct_object, start_offset, index_by_name): start_offset is the
    offset the struct must be unpacked from, and index_by_name maps each field name to its
    position in the tuple `unpack_from` returns.

    When `start_offset` is not given, it defaults to the lowest field offset, so the struct
    carries no unnecessary leading padding. Pass an explicit `start_offset` (for example 0,
    to always unpack from a fixed anchor position such as a record start) when the caller
    needs the struct to start somewhere at or before the lowest field.

    Raises:
        ValueError: `fields` is empty, two fields overlap, or an explicit `start_offset` is
            past the lowest field offset.
    """
    if not fields:
        raise ValueError("fields must not be empty")
    sorted_fields = sorted(fields, key=lambda described_field: described_field[0])
    lowest_offset = sorted_fields[0][0]
    if start_offset is None:
        start_offset = lowest_offset
    elif start_offset > lowest_offset:
        raise ValueError(
            f"start_offset {start_offset} is past the lowest field offset {lowest_offset}"
        )
    cursor = start_offset
    format_codes: list[str] = []
    index_by_name: dict[str, int] = {}
    for position, (offset, code, name) in enumerate(sorted_fields):
        gap = offset - cursor
        if gap < 0:
            raise ValueError(f"field {name!r} at offset {offset} overlaps an earlier field")
        if gap:
            format_codes.append(f"{gap}x")
        format_codes.append(code)
        cursor = offset + struct.calcsize(code)
        index_by_name[name] = position
    return struct.Struct("<" + "".join(format_codes)), start_offset, index_by_name
