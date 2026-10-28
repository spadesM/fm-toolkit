"""Save metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import ClassVar

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class SectionInfo:
    """One named section from the save's own directory.

    Attributes:
        name: Section name.
        extension: ".dat" or ".cmt".
        file_offset: Where the section's compressed frame starts in the file.
        compressed_size: Size of the compressed frame in bytes.
        decompressed_size: Size of the section once decompressed.
        schema: Schema number stored at the start of the section.
        unknown: Directory values without an identified meaning ("tail0", "tail1")
            (unconfirmed).
    """

    name: str
    extension: str
    file_offset: int
    compressed_size: int
    decompressed_size: int
    schema: int
    unknown: Mapping[str, int] = field(hash=False)

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("tail0", "tail1")


@dataclass(frozen=True, slots=True)
class SaveInfo:
    """Facts about a save, read when it is opened.

    The repr leaves out the save name, the summary strings and the section list.

    Attributes:
        game: Game edition, for example "FM26".
        build: Version and build that last wrote the save, for example "26.3.2+2329565".
        build_number: The numeric build.
        known_build: Whether fmsave has a full set of layout tables for this build.
        db_version: Game database version string stored in the save (unconfirmed).
        game_date: In-game date, falling back to the structured save summary before the first
            Continue when the normal clock is null; None when neither is readable (unconfirmed).
        time_slot: Intra-day time slot stored with the in-game date (unconfirmed).
        save_name: The save's own name. `fmsave info` hides it unless --show-name is passed.
        sections: Every named section in file order.
        summary_strings: The readable strings stored in the save summary, in file order,
            including the build string. They can hold the human manager's name and club and
            competition names, so `fmsave info` does not show them (unconfirmed).
        section_schemas: Schema number of every named section, read-only.
        file_name: The save's file name, without its folder.
    """

    game: str
    build: str
    build_number: int
    known_build: bool
    db_version: str
    game_date: date | None
    time_slot: int
    save_name: str = field(repr=False)
    sections: tuple[SectionInfo, ...] = field(repr=False)
    summary_strings: tuple[str, ...] = field(repr=False)
    section_schemas: Mapping[str, int] = field(hash=False)
    file_name: str


register_field_statuses(
    SectionInfo,
    verified=("name", "extension", "file_offset", "compressed_size", "decompressed_size", "schema"),
    unconfirmed=("unknown",),
)
register_field_statuses(
    SaveInfo,
    verified=(
        "game",
        "build",
        "build_number",
        "known_build",
        "save_name",
        "sections",
        "section_schemas",
        "file_name",
    ),
    unconfirmed=("db_version", "game_date", "time_slot", "summary_strings"),
)
