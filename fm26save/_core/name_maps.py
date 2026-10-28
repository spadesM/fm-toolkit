"""The user-supplied map from a competition's editor database id to its name.

No save holds a competition name: the game renders them from its own installed database. fmsave
therefore ships no names, reads no game install and makes no network call. What it does ship is
`Competition.database_id`, the competition's id in the game's editor database, which is the same
value in every save and is what every name source outside a save is keyed on. A reader who wants
names builds a map from that id once and passes it to `fmsave.open`, where it names competitions
in every save they own.

The map is keyed on the **database** id and never on the stage-space competition id, which
differs between saves and between databases.

Only the names in __all__ are public.
"""

from __future__ import annotations

import csv
import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from fm26save._core._frozen import FrozenMapping

__all__ = ["normalize_competition_names", "read_competition_names"]

_DATABASE_ID_COLUMN = 0
_NAME_COLUMN = 1
_EXPECTED_COLUMNS = 2

# What an error calls a path with no file name of its own, which no readable file has.
_UNNAMED_FILE = "the given file"

# What to tell a reader whose row split into more cells than it should have.
_EXTRA_COLUMN_HINT = "; put quotes around a name that holds a comma"

# The map of a save opened without one, shared because it is immutable and always empty.
_EMPTY_COMPETITION_NAMES: FrozenMapping[int, str] = FrozenMapping({})


def _error_file_name(path: str | os.PathLike[str]) -> str:
    """The file's own name, never the folder holding it.

    An error a reader pastes into a bug report must not carry any part of their directory
    layout. This is the rule the command line applies to the paths an OSError
    reports, repeated here so this module stays independent of the command line.
    """
    return Path(os.fspath(path)).name or _UNNAMED_FILE


def _is_blank(row: list[str]) -> bool:
    """Whether a row holds nothing: an empty line, or one of nothing but separators and spaces."""
    return all(not cell.strip() for cell in row)


def _parsed_database_id(cell: str) -> int | None:
    """The cell as a database id, or None when it is not one.

    Only plain ASCII digits count. `int` also reads a sign, underscore separators and the
    digits of other scripts, and none of those is a database id: a negative id is nonsense,
    and the rest let one id be written several ways, each looking up a key none of the others
    would. Turning them down here also keeps the header rule honest, since a first cell of
    `-1` is then read as the header it looks like rather than as a row.
    """
    return int(cell) if cell.isascii() and cell.isdigit() else None


def read_competition_names(path: str | os.PathLike[str]) -> dict[int, str]:
    """Read a two-column UTF-8 CSV of `database_id,name` into a competition name map.

    The first column is the competition's editor database id, which is what
    `Competition.database_id` carries. A first row whose first cell is not a whole number is
    taken for a header and skipped. Blank lines are skipped, and surrounding whitespace is
    stripped from both cells.

    One id may be listed twice with the same name. Two different names for one id are a
    contradiction and raise, because neither is more likely to be the one meant.

    A row is exactly two columns wide. A third column is a fault as much as a missing one,
    since the extra cell leaves the row ambiguous: a name that holds a comma belongs in
    quotes rather than spread across cells.

    Every error names the file and never the folder holding it, so a message a reader pastes
    into a bug report carries no part of their directory layout.

    Raises:
        OSError: The file cannot be opened or read. It is left to the caller, which knows the
            path it passed.
        ValueError: A row has other than two columns, an id is not a whole number, a name is
            empty, or one id is listed twice under two names.
    """
    file_name = _error_file_name(path)
    names: dict[int, str] = {}
    with open(path, encoding="utf-8", newline="") as name_file:
        rows = csv.reader(name_file)
        header_row_allowed = True
        for row in rows:
            # line_num counts physical lines, so a row whose quoted name holds a newline is
            # reported at the line it ended on rather than the line it began on. That is the
            # only line number the csv reader offers, and it is the line the row's closing
            # quote sits on in the reader's own editor.
            line_number = rows.line_num
            if _is_blank(row):
                continue
            first_cell = row[_DATABASE_ID_COLUMN].strip()
            if header_row_allowed:
                header_row_allowed = False
                if _parsed_database_id(first_cell) is None:
                    continue
            if len(row) != _EXPECTED_COLUMNS:
                # A row of more than two columns is refused as firmly as one of fewer. The
                # extra cell leaves the row ambiguous: nothing says whether the name was meant
                # to hold the comma or whether a column was added, and either guess would
                # store a name the reader never wrote. The hint says how to write such a name.
                hint = _EXTRA_COLUMN_HINT if len(row) > _EXPECTED_COLUMNS else ""
                raise ValueError(
                    f"{file_name} line {line_number}: expected {_EXPECTED_COLUMNS} columns, "
                    f"found {len(row)}{hint}"
                )
            database_id = _parsed_database_id(first_cell)
            if database_id is None:
                raise ValueError(
                    f"{file_name} line {line_number}: {first_cell!r} is not a competition "
                    "database id"
                )
            name = row[_NAME_COLUMN].strip()
            if not name:
                raise ValueError(f"{file_name} line {line_number}: the name is empty")
            listed_name = names.get(database_id)
            if listed_name is not None and listed_name != name:
                raise ValueError(
                    f"{file_name} line {line_number}: database id {database_id} is listed twice"
                )
            names[database_id] = name
    return names


def normalize_competition_names(
    names: Mapping[int, str] | str | os.PathLike[str] | None,
) -> Mapping[int, str]:
    """Turn whatever `fmsave.open` was given into one immutable map keyed on the database id.

    None gives an empty map, a path is read through `read_competition_names`, and a mapping is
    copied and checked. Both forms normalise a name the same way: surrounding whitespace is
    stripped, and a name with nothing left after that is empty and raises. A file and a
    mapping carrying the same text therefore give the same map, whichever a reader hands over,
    so nothing silently depends on which one they chose.

    The map that comes back holds its own copy of the items and cannot be changed, so a caller
    who wants a map they can edit should build a dict from it.

    Raises:
        OSError: A path was given and the file cannot be opened or read.
        TypeError: A key is not an int, or a name is not a str.
        ValueError: A name is empty, or a CSV was given and is malformed (see
            `read_competition_names`).
    """
    return _normalized_competition_names(names)


def _normalized_competition_names(
    names: Mapping[int, str] | str | os.PathLike[str] | None,
) -> FrozenMapping[int, str]:
    """The same map, typed as the immutable one fmsave itself holds.

    A save keeps the map for its whole life, so `fmsave.open` takes the frozen type rather
    than the plain `Mapping` the public annotation promises a caller.
    """
    if names is None:
        return _EMPTY_COMPETITION_NAMES
    if isinstance(names, (str, os.PathLike)):
        return FrozenMapping(read_competition_names(names))
    checked_names: dict[int, str] = {}
    # The declared type says what a caller should pass; these checks are what happens when one
    # passes something else, so the items are read back as plain objects to check them at all.
    for database_id, name in cast("Mapping[object, object]", names).items():
        if not isinstance(database_id, int) or isinstance(database_id, bool):
            raise TypeError(f"competition name key {database_id!r} is not a database id")
        if not isinstance(name, str):
            raise TypeError(f"the competition name for database id {database_id} is not a string")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError(f"the competition name for database id {database_id} is empty")
        checked_names[database_id] = stripped_name
    return FrozenMapping(checked_names)
