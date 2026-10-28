"""Game and build detection, and the metadata returned as `Save.info`."""

from __future__ import annotations

import os
import re
import struct
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import fm26save._core as fmsave
from fm26save._core._container import (
    ContainerIndex,
    damaged_part_error,
    read_section,
    read_section_heads,
)
from fm26save._core._errors import (
    ISSUES_URL,
    CorruptSaveError,
    ReaderCheckError,
    UnknownBuildWarning,
    UnsupportedGameError,
)
from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import (
    FALLBACK_BUILD,
    GameInfoLayout,
    SaveSummaryLayout,
    SummaryStringsLayout,
    find_layout,
    known_builds,
    registered_layouts,
)
from fm26save._core._package import __version__
from fm26save._core._scan import (
    decode_date,
    decode_time_slot,
    find_marker,
    read_length_prefixed_string,
    read_u16,
    read_u32,
)
from fm26save._core.models.meta import SaveInfo, SectionInfo
from fm26save._core.readers._common import SAVE_SUMMARY_SECTION
from fm26save._core.readers.managed import read_summary_strings

SUPPORTED_GAME_MAJOR = 26
SECTION_MAGIC_PREFIX = b"\x03\x01"
SECTION_HEAD_BYTES = 8
SCHEMA_OFFSET = 6
LENGTH_PREFIX_BYTES = 4
GAME_INFO_SECTION = "game_info"
VERSION_CANDIDATE_START = re.compile(rb"(?<![0-9.])[0-9]{1,3}\.")
MAX_MIGRATION_NAMES = 4096
MAX_MIGRATION_NAME_BYTES = 4096
UNSET_GAME_INFO_CLOCK = struct.pack("<HH", 1, 1900)


@dataclass(frozen=True, slots=True)
class GameVersion:
    major: int
    build: str
    build_number: int

    @property
    def game(self) -> str:
        return f"FM{self.major}"


@dataclass(frozen=True, slots=True)
class GameInfoFacts:
    db_version: str
    game_date: date | None
    time_slot: int


def section_schema(head: bytes, extension: str, section_name: str, file_name: str) -> int:
    expected_magic = SECTION_MAGIC_PREFIX + extension[::-1].encode("ascii")
    if len(head) < SECTION_HEAD_BYTES or head[: len(expected_magic)] != expected_magic:
        raise CorruptSaveError(
            f"{file_name}: section {section_name!r} does not start with a section signature"
        )
    return read_u16(head, SCHEMA_OFFSET)


def find_game_version(summary: bytes, layout: SaveSummaryLayout, file_name: str) -> GameVersion:
    """The first string whose u32 length prefix spans exactly a full version match."""
    version_pattern = re.compile(layout.version_pattern.encode("ascii"))
    for candidate in VERSION_CANDIDATE_START.finditer(summary):
        version_start = candidate.start()
        if version_start < LENGTH_PREFIX_BYTES:
            continue
        version_length = read_u32(summary, version_start - LENGTH_PREFIX_BYTES)
        version_end = version_start + version_length
        if (
            version_length == 0
            or version_length > layout.max_version_bytes
            or version_end > len(summary)
        ):
            continue
        version_match = version_pattern.fullmatch(summary, version_start, version_end)
        if version_match is None:
            continue
        return GameVersion(
            major=int(version_match.group(1)),
            build=version_match.group(0).decode("ascii"),
            build_number=int(version_match.group(4)),
        )
    raise UnsupportedGameError(
        f"{file_name}: no game version found. fmsave reads Football Manager 26 saves; for other versions see {ISSUES_URL}"
    )


@dataclass(frozen=True, slots=True)
class SummaryFacts:
    version: GameVersion
    summary_strings: tuple[str, ...]
    game_date: date | None
    time_slot: int = 0


def read_summary_clock(
    summary: bytes, layout: SaveSummaryLayout, version: GameVersion
) -> tuple[date, int] | None:
    """Read the structured summary clock, never a date-shaped byte scan.

    Schema 29 stores a setup string, build string, counted division names, an eight-byte
    manager header, manager and club names, club uid, then the date. A fresh career can have
    this date before `game_info` has a clock, and a continued career can retain an older
    internal clock. Other summary shapes remain readable for their version and strings,
    but cannot supply a displayed save clock.
    """
    try:
        _, offset = read_length_prefixed_string(
            summary, layout.structured_strings_offset, layout.max_setup_string_bytes
        )
        stored_version, offset = read_length_prefixed_string(
            summary, offset, layout.max_version_bytes
        )
        if stored_version != version.build:
            return None
        division_count = read_u32(summary, offset)
        if division_count > layout.max_divisions:
            return None
        offset += LENGTH_PREFIX_BYTES
        for _ in range(division_count):
            _, offset = read_length_prefixed_string(summary, offset, layout.max_summary_name_bytes)
        _, offset = read_length_prefixed_string(
            summary, offset + layout.manager_header_bytes, layout.max_summary_name_bytes
        )
        _, offset = read_length_prefixed_string(summary, offset, layout.max_summary_name_bytes)
        clock_at = offset + layout.club_uid_bytes
        game_date = decode_date(summary, clock_at)
        if game_date is None:
            return None
        return game_date, decode_time_slot(summary, clock_at)
    except CorruptSaveError:
        return None


def read_summary_facts(container_index: ContainerIndex) -> SummaryFacts:
    """Read the summary's version, strings and fallback date once, rejecting games other than FM26."""
    file_name = container_index.file_name
    summary = read_section(container_index, SAVE_SUMMARY_SECTION)
    summary_schema = section_schema(
        summary,
        container_index.sections[SAVE_SUMMARY_SECTION].extension,
        SAVE_SUMMARY_SECTION,
        file_name,
    )
    summary_layout = find_layout(SaveSummaryLayout, SAVE_SUMMARY_SECTION, summary_schema, "").layout
    version = find_game_version(summary, summary_layout, file_name)
    if version.major != SUPPORTED_GAME_MAJOR:
        raise UnsupportedGameError(
            f"{file_name} is an {version.game} save ({version.build}). fmsave {__version__} reads FM26 saves "
            f"only; {version.game} is not supported yet. See {ISSUES_URL}"
        )
    strings_layout = find_layout(
        SummaryStringsLayout, SAVE_SUMMARY_SECTION, summary_schema, ""
    ).layout
    clock = read_summary_clock(summary, summary_layout, version)
    return SummaryFacts(
        version,
        read_summary_strings(summary, strings_layout),
        None if clock is None else clock[0],
        0 if clock is None else clock[1],
    )


def decode_game_info(
    game_info: bytes, layout: GameInfoLayout, version: GameVersion, file_name: str
) -> GameInfoFacts:
    """Decode `game_info`; a read outside the section is reported with the file name."""
    try:
        return decode_game_info_fields(game_info, layout, version, file_name)
    except CorruptSaveError as error:
        raise damaged_part_error(file_name, GAME_INFO_SECTION, error) from error


def decode_game_info_fields(
    game_info: bytes, layout: GameInfoLayout, version: GameVersion, file_name: str
) -> GameInfoFacts:
    db_version, version_end = read_length_prefixed_string(
        game_info, layout.db_version_length_offset, layout.max_db_version_bytes
    )
    variable_bytes = game_info_filename_bytes(game_info, layout, version_end)
    stored_build_numbers = [
        read_u32(game_info, version_end + offset)
        for offset in layout.build_number_offsets_after_db_version
    ]
    window_start, window_end = layout.late_build_number_window_after_db_version
    late_build_number_at = find_marker(
        game_info,
        struct.pack("<I", version.build_number),
        version_end + variable_bytes + window_start,
        min(version_end + variable_bytes + window_end, len(game_info)),
    )
    mismatches: list[str] = []
    if any(
        stored_build_number != version.build_number for stored_build_number in stored_build_numbers
    ):
        mismatches.append("the saved-by build word holds another value")
    if late_build_number_at == -1:
        mismatches.append("no late build word sits inside its window")
    if mismatches:
        raise ReaderCheckError(
            f"{file_name}: game_info does not match build {version.build} "
            f"({' and '.join(mismatches)}), so the save layout differs from what fmsave expects. "
            f"Please report it at {ISSUES_URL}"
        )
    date_offset = version_end + variable_bytes + layout.game_date_offset_after_db_version
    return GameInfoFacts(
        db_version=db_version,
        game_date=decode_date(game_info, date_offset),
        time_slot=decode_time_slot(game_info, date_offset),
    )


def game_info_filename_bytes(game_info: bytes, layout: GameInfoLayout, version_end: int) -> int:
    """Walk the bounded filename list before the clock, without interpreting its strings."""
    count_offset = layout.filename_count_offset_after_db_version
    if count_offset is None:
        return 0
    count_at = version_end + count_offset
    count = read_u32(game_info, count_at)
    if count > layout.max_filenames:
        raise CorruptSaveError(
            f"game_info filename list claims {count} entries, more than {layout.max_filenames} allowed"
        )
    strings_start = count_at + LENGTH_PREFIX_BYTES
    cursor = strings_start
    for _ in range(count):
        _, cursor = read_length_prefixed_string(game_info, cursor, layout.max_filename_bytes)
    return cursor - strings_start


def game_info_migration_tail_fits(
    game_info: bytes, build_number: int, start: int, end: int
) -> bool:
    """Require one build marker followed by a bounded string list ending at the section end.

    A build-shaped word alone is insufficient evidence for a layout. Search only its
    existing window, and keep checking after a marker whose following list does not fit.
    """
    marker = struct.pack("<I", build_number)
    matches = 0
    while (build_at := find_marker(game_info, marker, start, end)) != -1:
        start = build_at + 1
        try:
            count = read_u32(game_info, build_at + LENGTH_PREFIX_BYTES)
            if count > MAX_MIGRATION_NAMES:
                continue
            cursor = build_at + 2 * LENGTH_PREFIX_BYTES
            for _ in range(count):
                _, cursor = read_length_prefixed_string(game_info, cursor, MAX_MIGRATION_NAME_BYTES)
            matches += cursor == len(game_info)
        except CorruptSaveError:
            continue
    return matches == 1


def checked_game_info_candidate(
    game_info: bytes, layout: GameInfoLayout, version: GameVersion, file_name: str
) -> GameInfoFacts:
    """Check a candidate's structured clock and migration tail, including explicit null clocks."""
    facts = decode_game_info(game_info, layout, version, file_name)
    _, version_end = read_length_prefixed_string(
        game_info, layout.db_version_length_offset, layout.max_db_version_bytes
    )
    base = version_end + game_info_filename_bytes(game_info, layout, version_end)
    clock_at = base + layout.game_date_offset_after_db_version
    clock_is_unset = game_info[clock_at : clock_at + 4] == UNSET_GAME_INFO_CLOCK
    start, end = layout.late_build_number_window_after_db_version
    if (facts.game_date is None and not clock_is_unset) or not game_info_migration_tail_fits(
        game_info, version.build_number, base + start, min(base + end, len(game_info))
    ):
        raise ReaderCheckError(
            f"{file_name}: game_info clock or migration list does not fit a verified layout "
            f"for build {version.build}. Please report it at {ISSUES_URL}"
        )
    return facts


def decode_unrecognized_game_info(
    game_info: bytes,
    preferred_layout: GameInfoLayout,
    schema: int | None,
    version: GameVersion,
    file_name: str,
) -> GameInfoFacts:
    """Choose a unique observed metadata shape without declaring other readers compatible.

    Only layouts registered for the same section schema are alternatives to the usual
    selection. No date scan, version-range guess or synthesized layout is used.
    """
    candidates = [preferred_layout]
    for entry in registered_layouts():
        if (
            entry.region == GAME_INFO_SECTION
            and entry.schema == schema
            and isinstance(entry.layout, GameInfoLayout)
            and entry.layout not in candidates
        ):
            candidates.append(entry.layout)
    matches: list[GameInfoFacts] = []
    preferred_error: CorruptSaveError | ReaderCheckError | None = None
    for candidate in candidates:
        try:
            matches.append(checked_game_info_candidate(game_info, candidate, version, file_name))
        except (CorruptSaveError, ReaderCheckError) as error:
            if candidate == preferred_layout:
                preferred_error = error
    if len(matches) == 1:
        return matches[0]
    if not matches and preferred_error is not None:
        raise preferred_error
    raise ReaderCheckError(
        f"{file_name}: game_info layout is ambiguous for build {version.build}. "
        f"Please report it at {ISSUES_URL}"
    )


def read_game_info_facts(
    container_index: ContainerIndex,
    section_schemas: Mapping[str, int],
    version: GameVersion,
    known_build: bool,
) -> GameInfoFacts:
    """Decode `game_info`; on a fallback layout, damage-shaped failures mean the layout does not fit."""
    file_name = container_index.file_name
    layout_match = find_layout(
        GameInfoLayout, GAME_INFO_SECTION, section_schemas.get(GAME_INFO_SECTION), version.build
    )
    game_info = read_section(container_index, GAME_INFO_SECTION)
    try:
        if not known_build:
            return decode_unrecognized_game_info(
                game_info,
                layout_match.layout,
                section_schemas.get(GAME_INFO_SECTION),
                version,
                file_name,
            )
        return decode_game_info(game_info, layout_match.layout, version, file_name)
    except CorruptSaveError as error:
        if known_build and layout_match.exact:
            raise
        raise ReaderCheckError(
            f"{file_name}: game_info does not fit the layout fmsave used for build {version.build}. "
            f"Please report it at {ISSUES_URL}"
        ) from error


def read_save_info(container_index: ContainerIndex) -> SaveInfo:
    """Detect the game and build and read save metadata. Warns on unknown FM26 builds."""
    file_name = container_index.file_name
    summary_facts = read_summary_facts(container_index)
    version = summary_facts.version
    known_build = version.build in known_builds()
    if not known_build:
        warnings.warn(
            UnknownBuildWarning(
                f"{file_name} was saved by FM26 build {version.build}, which fmsave {__version__} has no "
                "full set of layouts for. Metadata is checked against observed layouts; "
                f"other readers use the {FALLBACK_BUILD} layouts where it has none of its own. "
                "Readers check their results and raise ReaderCheckError if they do not fit."
            ),
            skip_file_prefixes=(str(Path(fmsave.__file__).parent) + os.sep,),
        )
    section_names = list(container_index.sections)
    heads = read_section_heads(container_index, section_names, SECTION_HEAD_BYTES)
    section_schemas = {
        name: section_schema(heads[name], container_index.sections[name].extension, name, file_name)
        for name in section_names
    }
    facts = read_game_info_facts(container_index, section_schemas, version, known_build)
    sections = tuple(
        SectionInfo(
            name=entry.name,
            extension=entry.extension,
            file_offset=entry.frame_offset,
            compressed_size=entry.compressed_size,
            decompressed_size=entry.decompressed_size,
            schema=section_schemas[entry.name],
            unknown=FrozenMapping(
                {"tail0": entry.trailing_values[0], "tail1": entry.trailing_values[1]}
            ),
        )
        for entry in container_index.sections.values()
    )
    return SaveInfo(
        game=version.game,
        build=version.build,
        build_number=version.build_number,
        known_build=known_build,
        db_version=facts.db_version,
        # The structured save summary is the displayed save clock. game_info can retain
        # the previous simulation day's clock; use both date and slot from one source.
        game_date=summary_facts.game_date
        if summary_facts.game_date is not None
        else facts.game_date,
        time_slot=summary_facts.time_slot
        if summary_facts.game_date is not None
        else facts.time_slot,
        save_name=container_index.save_name,
        sections=sections,
        summary_strings=summary_facts.summary_strings,
        section_schemas=FrozenMapping(section_schemas),
        file_name=file_name,
    )
