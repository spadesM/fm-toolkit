"""Comprehensive FM26 (.fm) Save Manipulator, In-Memory Editor & Lossless Container Repacker.

Supports inspecting, modifying, and repacking every value decoded across:
- All 28 core tables (`players`, `persons`, `name-pools`, `contracts`, `suspensions`, `clubs`,
  `managed-clubs`, `finances`, `sponsorships`, `facilities`, `stadiums`, `affiliates`, `staff`,
  `staff-lists`, `injuries`, `injury-types`, `tactics`, `set-pieces`, `training`, `mentoring`,
  `job-vacancies`, `competitions`, `stages`, `league-tables`, `fixtures`, `competition-rules`,
  `transfer-windows`, `player-match-stats`, `player-season-stats`, `player-season-history`)
- All enriched fields (`enrichment.py`: player squad number, RCA, PA copy, body type, relations,
  contract head/tail fees & clauses, staff 26 hidden coaching/scouting/medical attributes,
  post-finance facility/fanbase metrics, tactics 26-man lineup selectors)
- All extra sections (`extra_sections.py`: `hall_of_fame.dat`, `board_takeover_manager.dat`,
  `shortlist_man.dat`, `contract_man.dat`, `agent_manager.dat`, `news.dat`)
- All 81 top-level `.dat`/`.cmt` sections, `.apm`/`.scm` match files, and `"rgman"` sub-directory
  frames (`unlisted_after_non_pl_hist_ls` / `SPAN_REGION`).

Safety & Original File Protection:
- Never modifies the source `.fm` save file in place by default.
- Requires an explicit target `output_path` when saving (or creates a working copy first via
  `FM26Editor.create_working_copy`).
"""

from __future__ import annotations

import datetime
import shutil
import struct
from bisect import bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import zstandard as zstd

from fm26save import _core
from fm26save._core._container import (
    FILE_MAGIC,
    FRAME_BASE,
    HEADER_SIZE,
    MAX_SAVE_NAME_BYTES,
    TRAILER_HEADER_SIZE,
    TRAILER_POINTER_AT,
    DirectoryEntry,
    parse_directory_entry,
    read_index,
    read_length_prefixed_string,
)
from fm26save._core._layouts import (
    AffiliateGroupLayout,
    ClubRecordLayout,
    ClubStatusLayout,
    CompetitionIdPairLayout,
    ContractLayout,
    FacilityByteLayout,
    FinanceChainLayout,
    FixtureCalendarLayout,
    GameInfoLayout,
    HumansLayout,
    InjuryManagerLayout,
    InjuryTypeTableLayout,
    JobCentreLayout,
    LeagueTableLayout,
    MatchRecordLayout,
    MatchSummaryLayout,
    NamePoolLayout,
    PersonBlockLayout,
    PlayerRecordLayout,
    RulesPreambleLayout,
    SaveSummaryLayout,
    SeasonHistoryLayout,
    SeasonStatsLayout,
    SponsorChainLayout,
    StadiumTableLayout,
    StaffLayout,
    StageResultLayout,
    StageTableLayout,
    SuspensionLayout,
    TacticsLayout,
    TaggedStreamLayout,
    TeamListLayout,
    TrainingLayout,
    TransferWindowLayout,
    find_layout,
)
from fm26save._core._scan import (
    TIME_SLOT_SHIFT,
    decode_date,
    decode_time_slot,
    find_marker,
    iter_tagged_values,
    read_u16,
    read_u32,
    read_u64,
)
from fm26save._core._version import (
    GAME_INFO_SECTION,
    LENGTH_PREFIX_BYTES,
    SCHEMA_OFFSET,
    SECTION_HEAD_BYTES,
    find_game_version,
    game_info_filename_bytes,
    section_schema,
)
from fm26save._core.models.players import Trait as PlayerTrait
from fm26save._core.readers._common import (
    FEEDER_SECTION as AFFILIATE_SECTION,
    GAME_DB_SECTION,
    HUMANS_SECTION,
    INJURY_MANAGER_SECTION,
    JOB_CENTRE_SECTION,
    MATCH_FILE_REGION,
    MISSING_REFERENCE,
    SAVE_SUMMARY_SECTION,
    SPAN_REGION,
    TACTICS_SECTION,
    TRAINING_SECTION,
)
SEASON_HISTORY_SECTION = "player_stats_hist_dt"
from fm26save._core.readers.clubs import ClubLayouts, ClubRecordSpan, read_club_index
from fm26save._core.readers.contracts import build_contract_decoder
from fm26save._core.readers.finances import locate_finance_chain, locate_sponsor_chain
from fm26save._core.readers.names import locate_name_pools
from fm26save._core.readers.player_scan import locate_player_records
from fm26save._core.readers.results import result_search
from fm26save._core.readers.span import SpanRecords, find_span_layouts, scan_span
from fm26save._core.readers.stadiums import read_stadium_index
from fm26save._core.readers.staff import (
    locate_contracted_header,
    locate_human_header,
    locate_listed_header,
)
from fm26save._core.readers.stages import _row_decodes, _stage_table_scan, find_table_start


@dataclass(frozen=True, slots=True)
class _LocatedPersonBlock:
    birth_date_offset: int
    has_name_block: bool
    name_block_offset_from_birth: int


def locate_person_block(
    db: bytes | bytearray,
    window_start: int,
    window_end: int,
    person_layout: PersonBlockLayout,
    clock_year: int = 2050,
) -> _LocatedPersonBlock | None:
    """Locate a person's `PersonBlock` (`birth_date_offset` and `q` name block) inside `[window_start, window_end)`."""
    low_p, high_p = person_layout.personality_range
    p_cnt = person_layout.personality_count
    p_off_from_birth = person_layout.personality_offset_from_birth
    zero_off_from_birth = p_off_from_birth - 1
    zero_reg_off = person_layout.date_zero_bytes_offset_from_birth
    zero_reg_bytes = bytes(person_layout.date_zero_bytes_count)

    search_from = max(0, window_start + zero_off_from_birth)
    search_to = min(len(db) - p_cnt - 1, window_end - p_cnt - 1)
    pos = search_from
    while pos < search_to:
        if db[pos] == 0 and all(low_p <= db[pos + 1 + k] <= high_p for k in range(p_cnt)):
            b_off = pos - zero_off_from_birth
            if b_off >= 4 and b_off + zero_reg_off + len(zero_reg_bytes) <= len(db):
                raw_birth_word = read_u32(db, b_off)
                packed = raw_birth_word & 0xFFFF
                year = raw_birth_word >> 16
                day_of_year = packed & 0x1FF
                if (
                    (packed >> TIME_SLOT_SHIFT) == 0
                    and 1 <= day_of_year <= 366
                    and 1901 <= year <= clock_year
                    and db[b_off + zero_reg_off : b_off + zero_reg_off + len(zero_reg_bytes)] == zero_reg_bytes
                ):
                    legal_len: int | None = None
                    if read_u32(db, b_off - 4) == 0:
                        legal_len = 0
                    else:
                        min_l = person_layout.legal_name_length_min
                        max_l = person_layout.legal_name_length_max
                        for cand_l in range(min_l, max_l + 1):
                            if b_off - 4 - cand_l >= 0 and read_u32(db, b_off - 4 - cand_l) == cand_l:
                                legal_len = cand_l
                                break
                    if legal_len is not None:
                        block_start = b_off - person_layout.legal_name_offset_from_block_start - legal_len
                        tb_at = block_start + person_layout.trait_bits_offset_from_block_start
                        if (
                            tb_at >= 0
                            and block_start + 15 <= len(db)
                            and db[block_start + 4] == 0
                            and db[block_start + 9] == 0
                            and db[block_start + 14] == 0
                        ):
                            fn_id = read_u32(db, block_start)
                            sn_id = read_u32(db, block_start + 5)
                            cn_id = read_u32(db, block_start + 10)
                            limit = person_layout.name_id_limit
                            if (
                                (fn_id == MISSING_REFERENCE or fn_id < limit)
                                and (sn_id == MISSING_REFERENCE or sn_id < limit)
                                and (cn_id == MISSING_REFERENCE or cn_id < limit)
                            ):
                                return _LocatedPersonBlock(
                                    birth_date_offset=b_off,
                                    has_name_block=True,
                                    name_block_offset_from_birth=block_start - b_off,
                                )
        pos += 1
    return None

NULL_DATE_BYTES = struct.pack("<HH", 1, 1900)
FF_DATE_BYTES = b"\xff\xff\xff\xff"


def _coerce_date(value: datetime.date | str | None) -> datetime.date | None:
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value).strip())


def _coerce_time(value: datetime.time | str | None) -> datetime.time | None:
    if value is None:
        return None
    if isinstance(value, datetime.time):
        return value
    text = str(value).strip()
    parts = text.split(":")
    return datetime.time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def encode_packed_date(
    d: datetime.date | str | None,
    time_slot: int = 0,
    null_bytes: bytes = NULL_DATE_BYTES,
) -> bytes:
    """Encode a `datetime.date` (or ISO string) and time slot (0..127) into FM26's 4-byte date format."""
    coerced = _coerce_date(d)
    if coerced is None:
        return null_bytes
    day_of_year = coerced.timetuple().tm_yday
    slot = max(0, min(127, int(time_slot)))
    packed_low = (slot << TIME_SLOT_SHIFT) | (day_of_year & 0x1FF)
    return struct.pack("<HH", packed_low, coerced.year)


def write_packed_date_into(
    buf: bytearray,
    offset: int,
    d: datetime.date | str | None,
    time_slot: int | None = None,
    null_bytes: bytes = NULL_DATE_BYTES,
) -> None:
    """Write a 4-byte packed date into `buf` at `offset`, preserving existing time_slot if `time_slot` is None."""
    if d is None:
        buf[offset : offset + 4] = null_bytes
        return
    if time_slot is None:
        existing_date = decode_date(buf, offset)
        slot = decode_time_slot(buf, offset) if existing_date is not None else 0
    else:
        slot = time_slot
    buf[offset : offset + 4] = encode_packed_date(d, time_slot=slot, null_bytes=null_bytes)


def encode_kick_off_words(
    d: datetime.date | str,
    kick_off_time: datetime.time | str | None,
    layout: FixtureCalendarLayout,
    existing_packed_kick_off: int | None = None,
) -> tuple[int, int]:
    """Encode a fixture kick-off date and time into `(packed_kick_off, kick_off_year)`."""
    coerced_date = _coerce_date(d)
    if coerced_date is None:
        raise ValueError("Fixture date cannot be None")
    day_of_year = coerced_date.timetuple().tm_yday
    coerced_time = _coerce_time(kick_off_time)
    if coerced_time is not None:
        total_minutes = coerced_time.hour * 60 + coerced_time.minute
        slot = (total_minutes // layout.kick_off_slot_minutes) - layout.kick_off_slot_offset
        slot = max(0, min(127, slot))
    elif existing_packed_kick_off is not None:
        slot = existing_packed_kick_off >> TIME_SLOT_SHIFT
    else:
        slot = (15 * 60 // layout.kick_off_slot_minutes) - layout.kick_off_slot_offset
    packed_kick_off = (slot << TIME_SLOT_SHIFT) | (day_of_year & 0x1FF)
    return packed_kick_off, coerced_date.year


@dataclass(slots=True)
class _SubDirectory:
    name: str
    entries: list[DirectoryEntry]


@dataclass(slots=True)
class _ParsedTrailer:
    trailer_offset: int
    trailer_magic_header: bytes
    save_name: str
    top_entries: list[DirectoryEntry]
    sub_directories: list[_SubDirectory]
    tail_bytes: bytes


def _parse_full_trailer(save_path: Path) -> tuple[bytes, _ParsedTrailer]:
    """Read the 26-byte outer header and parse the entire trailer directory including subdirectories."""
    with save_path.open("rb") as f:
        header = f.read(HEADER_SIZE)
        if len(header) != HEADER_SIZE or header[: len(FILE_MAGIC)] != FILE_MAGIC:
            raise ValueError(f"{save_path.name} is not a valid FM26 save file")
        dir_rel = read_u64(header, TRAILER_POINTER_AT)
        trailer_offset = TRAILER_POINTER_AT + dir_rel
        f.seek(trailer_offset)
        trailer_bytes = f.read()

    trailer_magic_header = trailer_bytes[:TRAILER_HEADER_SIZE]
    trailer_compressed = trailer_bytes[TRAILER_HEADER_SIZE:]
    dctx = zstd.ZstdDecompressor()
    trailer_payload = dctx.decompress(trailer_compressed, max_output_size=64 * 1024 * 1024)

    save_name, cursor = read_length_prefixed_string(trailer_payload, 0, MAX_SAVE_NAME_BYTES)
    top_count = read_u32(trailer_payload, cursor)
    cursor += 4
    top_entries: list[DirectoryEntry] = []
    for _ in range(top_count):
        parsed = parse_directory_entry(trailer_payload, cursor)
        if parsed is None:
            raise ValueError(f"{save_path.name}: failed to parse top-level directory entry at {cursor}")
        entry, cursor = parsed
        top_entries.append(entry)

    sub_directories: list[_SubDirectory] = []
    if cursor + 4 <= len(trailer_payload):
        # Peek to see if there is a subdirectory count followed by a valid subdirectory name
        sub_dir_count = read_u32(trailer_payload, cursor)
        if 0 < sub_dir_count <= 32 and cursor + 8 <= len(trailer_payload):
            cursor += 4
            for _ in range(sub_dir_count):
                sub_name, cursor = read_length_prefixed_string(trailer_payload, cursor, 256)
                sub_entry_count = read_u32(trailer_payload, cursor)
                cursor += 4
                sub_entries: list[DirectoryEntry] = []
                for _ in range(sub_entry_count):
                    parsed = parse_directory_entry(trailer_payload, cursor)
                    if parsed is None:
                        raise ValueError(
                            f"{save_path.name}: failed to parse subdirectory {sub_name!r} entry at {cursor}"
                        )
                    entry, cursor = parsed
                    sub_entries.append(entry)
                sub_directories.append(_SubDirectory(name=sub_name, entries=sub_entries))

    tail_bytes = trailer_payload[cursor:]
    return header, _ParsedTrailer(
        trailer_offset=trailer_offset,
        trailer_magic_header=trailer_magic_header,
        save_name=save_name,
        top_entries=top_entries,
        sub_directories=sub_directories,
        tail_bytes=tail_bytes,
    )


def _serialize_directory_entry(entry: DirectoryEntry) -> bytes:
    name_bytes = entry.name.encode("ascii")
    ext_bytes = entry.extension.encode("ascii")
    rel_offset = entry.frame_offset - FRAME_BASE
    return (
        struct.pack("<I", len(name_bytes))
        + name_bytes
        + struct.pack("<I", len(ext_bytes))
        + ext_bytes
        + struct.pack(
            "<5Q",
            rel_offset,
            entry.compressed_size,
            entry.decompressed_size,
            entry.trailing_values[0],
            entry.trailing_values[1],
        )
    )


def _serialize_trailer_payload(trailer: _ParsedTrailer) -> bytes:
    parts: list[bytes] = []
    save_name_bytes = trailer.save_name.encode("utf-8")
    parts.append(struct.pack("<I", len(save_name_bytes)))
    parts.append(save_name_bytes)
    parts.append(struct.pack("<I", len(trailer.top_entries)))
    for entry in trailer.top_entries:
        parts.append(_serialize_directory_entry(entry))
    if trailer.sub_directories:
        parts.append(struct.pack("<I", len(trailer.sub_directories)))
        for sub in trailer.sub_directories:
            sub_name_bytes = sub.name.encode("utf-8")
            parts.append(struct.pack("<I", len(sub_name_bytes)))
            parts.append(sub_name_bytes)
            parts.append(struct.pack("<I", len(sub.entries)))
            for entry in sub.entries:
                parts.append(_serialize_directory_entry(entry))
    parts.append(trailer.tail_bytes)
    return b"".join(parts)


class FM26Editor:
    """In-memory FM26 (.fm) save manipulator and lossless container repacker.

    Protects the original save file by refusing to overwrite `source_path` in place unless
    `allow_overwrite_with_backup=True` is explicitly passed (which creates a `.orig.bak` backup
    before atomic replacement).
    """

    def __init__(self, save_path: str | Path) -> None:
        self.source_path = Path(save_path).resolve()
        if not self.source_path.exists():
            raise FileNotFoundError(f"Save file not found: {self.source_path}")
        self._outer_header, self._trailer = _parse_full_trailer(self.source_path)
        self._container_index = read_index(self.source_path)
        self._save_reader = _core.open(self.source_path)
        self.core_save = self._save_reader
        self.version = self._save_reader.info
        self._build = self._save_reader.info.build
        self._game_db_schema = self._save_reader.info.section_schemas.get(GAME_DB_SECTION, 4000)

        # Keyed by original frame_offset -> modified bytearray
        self._modified_frames: dict[int, bytearray] = {}
        self._edit_log: list[dict[str, Any]] = []

        # Cached structural indexes on current game_db buffer
        self._cached_club_index: Any = None
        self._cached_player_records: Any = None
        self._cached_stadium_index: Any = None
        self._cached_span_records: SpanRecords | None = None

    def get_game_date(self) -> datetime.date | None:
        """Return the current in-game clock date (reading from `save_game_summary.dat` and `game_info.dat`)."""
        try:
            summary_buf = self.get_section_buffer(SAVE_SUMMARY_SECTION)
            summary_schema = read_u16(summary_buf, SCHEMA_OFFSET)
            summary_layout = self._layout(SaveSummaryLayout, SAVE_SUMMARY_SECTION, summary_schema)
            version = find_game_version(summary_buf, summary_layout, self.source_path.name)
            _, offset = read_length_prefixed_string(
                summary_buf, summary_layout.structured_strings_offset, summary_layout.max_setup_string_bytes
            )
            stored_ver, offset = read_length_prefixed_string(
                summary_buf, offset, summary_layout.max_version_bytes
            )
            if stored_ver == version.build:
                div_count = read_u32(summary_buf, offset)
                offset += LENGTH_PREFIX_BYTES
                for _ in range(div_count):
                    _, offset = read_length_prefixed_string(
                        summary_buf, offset, summary_layout.max_summary_name_bytes
                    )
                _, offset = read_length_prefixed_string(
                    summary_buf, offset + summary_layout.manager_header_bytes, summary_layout.max_summary_name_bytes
                )
                _, offset = read_length_prefixed_string(
                    summary_buf, offset, summary_layout.max_summary_name_bytes
                )
                clock_at = offset + summary_layout.club_uid_bytes
                d_sum = decode_date(summary_buf, clock_at)
                if d_sum is not None:
                    return d_sum
        except Exception:
            pass
        try:
            gi_buf = self.get_section_buffer(GAME_INFO_SECTION)
            gi_schema = read_u16(gi_buf, SCHEMA_OFFSET)
            gi_layout = self._layout(GameInfoLayout, GAME_INFO_SECTION, gi_schema)
            _, after_db_ver = read_length_prefixed_string(
                gi_buf, gi_layout.db_version_length_offset, gi_layout.max_db_version_bytes
            )
            fn_shift = game_info_filename_bytes(gi_buf, gi_layout, after_db_ver)
            clock_offset = after_db_ver + gi_layout.game_date_offset_after_db_version + fn_shift
            d = decode_date(gi_buf, clock_offset)
            if d is not None:
                return d
        except Exception:
            pass
        return self._save_reader.info.game_date

    @classmethod
    def create_working_copy(cls, src_path: str | Path, dst_path: str | Path) -> FM26Editor:
        """Copy an existing `.fm` save file to `dst_path` and open an `FM26Editor` on the copy."""
        src = Path(src_path).resolve()
        dst = Path(dst_path).resolve()
        if src == dst:
            raise ValueError("Working copy destination path must differ from source save path")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return cls(dst)

    def close(self) -> None:
        self._save_reader.close()

    def __enter__(self) -> FM26Editor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def edit_log(self) -> list[dict[str, Any]]:
        """Chronological log of all mutations applied in this editor session."""
        return list(self._edit_log)

    def _invalidate_db_caches(self) -> None:
        self._cached_club_index = None
        self._cached_player_records = None
        self._cached_stadium_index = None

    # ------------------------------------------------------------------
    # Low-Level Frame, Section & Subdirectory ("rgman" / SPAN_REGION) IO
    # ------------------------------------------------------------------
    def _find_top_entry(self, name: str, extension: str | None = None) -> DirectoryEntry:
        stem = name
        ext = extension
        if ext is None and "." in name:
            idx = name.rfind(".")
            stem, ext = name[:idx], name[idx:]
        for entry in self._trailer.top_entries:
            if entry.name == stem and (ext is None or entry.extension == ext):
                return entry
        for sub in self._trailer.sub_directories:
            for entry in sub.entries:
                if entry.name == stem and (ext is None or entry.extension == ext):
                    return entry
        raise KeyError(f"Directory entry {name!r} not found in container")

    def _get_entry_buffer(self, entry: DirectoryEntry) -> bytearray:
        buf = self._modified_frames.get(entry.frame_offset)
        if buf is not None:
            return buf
        with self.source_path.open("rb") as f:
            f.seek(entry.frame_offset)
            compressed = f.read(entry.compressed_size)
        dctx = zstd.ZstdDecompressor()
        raw = dctx.decompress(compressed, max_output_size=max(entry.decompressed_size + 1024, 64 * 1024))
        buf = bytearray(raw)
        self._modified_frames[entry.frame_offset] = buf
        return buf

    def get_section_buffer(self, section_name: str) -> bytearray:
        """Return a mutable `bytearray` for any top-level or `"rgman"` section (marks it modified)."""
        entry = self._find_top_entry(section_name)
        return self._get_entry_buffer(entry)

    def set_section_bytes(self, section_name: str, data: bytes | bytearray) -> None:
        """Replace the entire decompressed payload of `section_name`."""
        entry = self._find_top_entry(section_name)
        self._modified_frames[entry.frame_offset] = bytearray(data)
        if entry.name == GAME_DB_SECTION:
            self._invalidate_db_caches()
        self._edit_log.append(
            {"type": "set_section_bytes", "section": f"{entry.name}{entry.extension}", "size": len(data)}
        )

    def patch_section_bytes(
        self, section_name: str, offset: int, patch: bytes | bytearray
    ) -> bytes:
        """Patch `patch` bytes into `section_name` at `offset`, returning the previous bytes."""
        buf = self.get_section_buffer(section_name)
        if offset < 0 or offset + len(patch) > len(buf):
            raise ValueError(
                f"Patch range [{offset}..{offset + len(patch)}) out of bounds for {section_name} ({len(buf)} bytes)"
            )
        old = bytes(buf[offset : offset + len(patch)])
        buf[offset : offset + len(patch)] = patch
        if section_name.startswith(GAME_DB_SECTION):
            self._invalidate_db_caches()
        self._edit_log.append(
            {
                "type": "patch_section_bytes",
                "section": section_name,
                "offset": offset,
                "old_hex": old.hex(),
                "new_hex": bytes(patch).hex(),
            }
        )
        return old

    def _rgman_intervals(self) -> list[tuple[int, int, DirectoryEntry]]:
        """Return `(span_start, span_end, entry)` for all entries in `"rgman"` (`SPAN_REGION`)
        ordered by physical `frame_offset` to match `walk_frames(idx, SPAN_REGION)`.
        """
        intervals: list[tuple[int, int, DirectoryEntry]] = []
        span_cursor = 0
        for sub in self._trailer.sub_directories:
            if sub.name == "rgman":
                for entry in sorted(sub.entries, key=lambda e: e.frame_offset):
                    curr_size = (
                        len(self._modified_frames[entry.frame_offset])
                        if entry.frame_offset in self._modified_frames
                        else entry.decompressed_size
                    )
                    intervals.append((span_cursor, span_cursor + curr_size, entry))
                    span_cursor += curr_size
        return intervals

    def _iter_rgman_frames(self) -> Iterable[bytes]:
        """Yield decompressed bytes for all frames in `"rgman"` (`SPAN_REGION`) in physical file order."""
        dctx = zstd.ZstdDecompressor()
        with self.source_path.open("rb") as f:
            for _start, _end, entry in self._rgman_intervals():
                if entry.frame_offset in self._modified_frames:
                    yield bytes(self._modified_frames[entry.frame_offset])
                else:
                    f.seek(entry.frame_offset)
                    comp = f.read(entry.compressed_size)
                    yield dctx.decompress(
                        comp, max_output_size=max(entry.decompressed_size + 1024, 64 * 1024)
                    )

    def _scan_span_records(self, *, force_rescan: bool = False) -> SpanRecords:
        """Scan `SPAN_REGION` across current (possibly modified) `"rgman"` frames."""
        if self._cached_span_records is None or force_rescan:
            clock = self.get_game_date() or datetime.date(2025, 7, 1)
            self._cached_span_records = scan_span(
                self._iter_rgman_frames(),
                find_span_layouts(self.version.build),
                clock,
                self.source_path.name,
            )
        return self._cached_span_records

    def _locate_span_entry(self, span_offset: int) -> tuple[DirectoryEntry, int]:
        """Map a `SPAN_REGION` relative offset to `(DirectoryEntry, offset_within_entry)`."""
        for start, end, entry in self._rgman_intervals():
            if start <= span_offset < end:
                return entry, span_offset - start
        raise ValueError(f"Span offset {span_offset} is outside the rgman / SPAN_REGION bounds")

    def read_span_bytes(self, span_offset: int, length: int) -> bytes:
        """Read `length` bytes starting at `span_offset` inside `SPAN_REGION`."""
        entry, rel_offset = self._locate_span_entry(span_offset)
        buf = self._get_entry_buffer(entry)
        return bytes(buf[rel_offset : rel_offset + length])

    def patch_span_bytes(self, span_offset: int, patch: bytes | bytearray) -> bytes:
        """Patch bytes at `span_offset` inside `SPAN_REGION` (`unlisted_after_non_pl_hist_ls`)."""
        entry, rel_offset = self._locate_span_entry(span_offset)
        buf = self._get_entry_buffer(entry)
        if rel_offset + len(patch) > len(buf):
            raise ValueError("Span patch crosses frame boundary")
        old = bytes(buf[rel_offset : rel_offset + len(patch)])
        buf[rel_offset : rel_offset + len(patch)] = patch
        return old

    # ------------------------------------------------------------------
    # Lossless Container Repacker & Save Writer
    # ------------------------------------------------------------------
    def save(
        self,
        output_path: str | Path,
        *,
        save_name: str | None = None,
        compression_level: int = 3,
        validate_output: bool = True,
        allow_overwrite_with_backup: bool = False,
    ) -> dict[str, Any]:
        """Repack all sections, subdirectories, headers, and trailer into a valid `.fm` file.

        Args:
            output_path: Target path for the modified `.fm` save file.
            save_name: Optional override for the trailer directory save name (defaults to `output_path.stem`).
            compression_level: Zstandard compression level for modified frames (default 3).
            validate_output: If True, runs `validate_save(output_path)` on the written file.
            allow_overwrite_with_backup: If False (default), refuses to overwrite `self.source_path`
                in place so original saves can never be accidentally corrupted. If True, creates
                a `.orig.bak` copy first before atomic replacement.
        """
        out_path = Path(output_path).resolve()
        backup_created: str | None = None
        if out_path == self.source_path:
            if not allow_overwrite_with_backup:
                raise ValueError(
                    f"Original save protection: refusing to overwrite source file {self.source_path} directly. "
                    "Pass a new output_path (e.g. a copy) or set allow_overwrite_with_backup=True."
                )
            bak_path = self.source_path.with_suffix(".orig.bak")
            if not bak_path.exists():
                shutil.copy2(self.source_path, bak_path)
            backup_created = str(bak_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp_repack")

        # Collect all directory entries (top-level + subdirectories) with references back to their lists
        indexed_entries: list[tuple[str, int, DirectoryEntry]] = []
        for idx, entry in enumerate(self._trailer.top_entries):
            indexed_entries.append(("top", idx, entry))
        for sub in self._trailer.sub_directories:
            for idx, entry in enumerate(sub.entries):
                indexed_entries.append((sub.name, idx, entry))

        # Sort by physical frame_offset in the source file
        indexed_entries.sort(key=lambda item: item[2].frame_offset)

        # Match FM26's native Zstandard frame descriptor (0x04: content checksum enabled, no content size header)
        cctx = zstd.ZstdCompressor(
            level=compression_level,
            write_checksum=True,
            write_content_size=False,
            write_dict_id=False,
        )

        updated_top: dict[int, DirectoryEntry] = {}
        updated_sub: dict[tuple[str, int], DirectoryEntry] = {}
        recompressed_count = 0

        with self.source_path.open("rb") as src_f, tmp_path.open("wb") as dst_f:
            # Write placeholder 26-byte header first
            dst_f.write(self._outer_header)
            src_cursor = HEADER_SIZE
            dst_cursor = HEADER_SIZE

            for group, list_idx, entry in indexed_entries:
                # Copy any unlisted gap before this entry if one ever exists
                if entry.frame_offset > src_cursor:
                    gap_len = entry.frame_offset - src_cursor
                    src_f.seek(src_cursor)
                    dst_f.write(src_f.read(gap_len))
                    dst_cursor += gap_len
                    src_cursor = entry.frame_offset

                new_frame_offset = dst_cursor
                if entry.frame_offset in self._modified_frames:
                    decomp_buf = self._modified_frames[entry.frame_offset]
                    comp_bytes = cctx.compress(bytes(decomp_buf))
                    dst_f.write(comp_bytes)
                    new_comp_size = len(comp_bytes)
                    new_decomp_size = len(decomp_buf)
                    recompressed_count += 1
                else:
                    src_f.seek(entry.frame_offset)
                    comp_bytes = src_f.read(entry.compressed_size)
                    dst_f.write(comp_bytes)
                    new_comp_size = entry.compressed_size
                    new_decomp_size = entry.decompressed_size

                dst_cursor += new_comp_size
                src_cursor = entry.frame_end

                new_entry = DirectoryEntry(
                    name=entry.name,
                    extension=entry.extension,
                    frame_offset=new_frame_offset,
                    compressed_size=new_comp_size,
                    decompressed_size=new_decomp_size,
                    trailing_values=entry.trailing_values,
                )
                if group == "top":
                    updated_top[list_idx] = new_entry
                else:
                    updated_sub[(group, list_idx)] = new_entry

            # Copy any trailing bytes between last entry and trailer_offset if present
            if self._trailer.trailer_offset > src_cursor:
                rem_len = self._trailer.trailer_offset - src_cursor
                src_f.seek(src_cursor)
                dst_f.write(src_f.read(rem_len))
                dst_cursor += rem_len

            new_trailer_offset = dst_cursor
            if save_name is not None:
                new_save_name = save_name
            elif any(e.get("type") == "set_save_name" for e in self._edit_log):
                new_save_name = self._trailer.save_name
            else:
                new_save_name = out_path.stem
            new_trailer = _ParsedTrailer(
                trailer_offset=new_trailer_offset,
                trailer_magic_header=self._trailer.trailer_magic_header,
                save_name=new_save_name,
                top_entries=[updated_top[i] for i in range(len(self._trailer.top_entries))],
                sub_directories=[
                    _SubDirectory(
                        name=sub.name,
                        entries=[updated_sub[(sub.name, i)] for i in range(len(sub.entries))],
                    )
                    for sub in self._trailer.sub_directories
                ],
                tail_bytes=self._trailer.tail_bytes,
            )
            trailer_payload = _serialize_trailer_payload(new_trailer)
            trailer_compressed = cctx.compress(trailer_payload)
            dst_f.write(self._trailer.trailer_magic_header)
            dst_f.write(trailer_compressed)

            # Update 26-byte outer header: preserve 0..9 and 17..26, write directory_offset_rel at 9..17
            new_header = bytearray(self._outer_header)
            struct.pack_into("<Q", new_header, TRAILER_POINTER_AT, new_trailer_offset - TRAILER_POINTER_AT)
            dst_f.seek(0)
            dst_f.write(new_header)

        tmp_path.replace(out_path)

        validation_passed: bool | None = None
        if validate_output:
            with _core.open(out_path) as check_sv:
                report = _core.validate_save(check_sv)
                validation_passed = all(r.status == "ok" for r in report.readers)

        return {
            "output_path": str(out_path),
            "source_path": str(self.source_path),
            "backup_created": backup_created,
            "save_name": new_save_name,
            "file_size": out_path.stat().st_size,
            "trailer_offset": new_trailer_offset,
            "recompressed_frames": recompressed_count,
            "edits_applied": len(self._edit_log),
            "validation_passed": validation_passed,
        }

    # ------------------------------------------------------------------
    # Internal Layout & Index Accessors
    # ------------------------------------------------------------------
    def _layout(self, layout_type: type[Any], region: str = GAME_DB_SECTION, schema: int | None = None) -> Any:
        eff_schema = self._game_db_schema if (region == GAME_DB_SECTION and schema is None) else schema
        if eff_schema is None and region in self._save_reader.info.section_schemas:
            eff_schema = self._save_reader.info.section_schemas[region]
        return find_layout(layout_type, region, eff_schema, self._build).layout

    def _game_db_buf(self) -> bytearray:
        return self.get_section_buffer(GAME_DB_SECTION)

    def _club_index(self) -> Any:
        if self._cached_club_index is None:
            db = self._game_db_buf()
            club_layout = self._layout(ClubRecordLayout)
            team_layout = self._layout(TeamListLayout)
            status_layout = self._layout(ClubStatusLayout)
            layouts = ClubLayouts(
                records=club_layout,
                team_lists=team_layout,
                statuses=status_layout,
            )
            self._cached_club_index = read_club_index(db, layouts, self.source_path.name)
        return self._cached_club_index

    def _club_span(self, club_uid: int) -> ClubRecordSpan:
        cidx = self._club_index()
        for sp in cidx.record_spans:
            if sp.club_uid == club_uid:
                return sp
        raise KeyError(f"ClubRecordSpan not found for club_uid={club_uid}")

    def _club_index_for_uid(self, club_uid: int) -> int:
        cidx = self._club_index()
        for c_index, c_uid in cidx.uid_by_club_index.items():
            if c_uid == club_uid:
                return c_index
        raise KeyError(f"Club index not found for club_uid={club_uid}")

    def _player_records(self) -> Any:
        if self._cached_player_records is None:
            db = self._game_db_buf()
            pool_layout = self._layout(NamePoolLayout)
            player_layout = self._layout(PlayerRecordLayout)
            pools = locate_name_pools(db, pool_layout, self.source_path.name)
            scan_start = pools.end_offset if pools is not None else 0
            self._cached_player_records = locate_player_records(
                db, scan_start, player_layout, self.source_path.name
            )
        return self._cached_player_records

    def _stadium_index(self) -> Any:
        if self._cached_stadium_index is None:
            db = self._game_db_buf()
            stadium_layout = self._layout(StadiumTableLayout)
            self._cached_stadium_index = read_stadium_index(
                db, stadium_layout, self.source_path.name
            )
        return self._cached_stadium_index

    def _resolve_player_position(self, player_uid_or_name: int | str) -> tuple[int, int, int]:
        """Resolve a player by UID, pindex, or name substring to `(record_index, record_offset, uid)`."""
        prec = self._player_records()
        if isinstance(player_uid_or_name, int):
            if player_uid_or_name in prec.position_by_uid:
                pos = prec.position_by_uid[player_uid_or_name]
                return pos, prec.record_offsets[pos], prec.uids[pos]
            if player_uid_or_name in prec.position_by_pindex:
                pos = prec.position_by_pindex[player_uid_or_name]
                return pos, prec.record_offsets[pos], prec.uids[pos]
            raise KeyError(f"Player with UID or pindex {player_uid_or_name} not found")

        q = player_uid_or_name.strip().lower()
        if q.isdigit():
            return self._resolve_player_position(int(q))
        players_table = self._save_reader.players()
        exact_hit = None
        partial_hit = None
        for p in players_table:
            for candidate in (p.name, p.full_name, p.common_name, p.legal_name):
                if candidate:
                    cl = candidate.lower()
                    if cl == q:
                        exact_hit = p.uid
                        break
                    if partial_hit is None and q in cl:
                        partial_hit = p.uid
            if exact_hit is not None:
                break
        target_uid = exact_hit if exact_hit is not None else partial_hit
        if target_uid is None:
            raise KeyError(f"No player matching {player_uid_or_name!r} found")
        pos = prec.position_by_uid[target_uid]
        return pos, prec.record_offsets[pos], prec.uids[pos]

    def _resolve_club_record(self, club_uid_or_name: int | str) -> Any:
        """Resolve a club by UID, club index, or name/short_name to its `Club` record."""
        cidx = self._club_index()
        if isinstance(club_uid_or_name, int):
            if club_uid_or_name in cidx.club_by_uid:
                return cidx.club_by_uid[club_uid_or_name]
            if club_uid_or_name in cidx.uid_by_club_index:
                return cidx.club_by_uid[cidx.uid_by_club_index[club_uid_or_name]]
            if club_uid_or_name in cidx.team_to_club:
                cuid, _slot = cidx.team_to_club[club_uid_or_name]
                return cidx.club_by_uid[cuid]
            raise KeyError(f"Club with UID/index/team_id {club_uid_or_name} not found")

        q = club_uid_or_name.strip().lower()
        if q.isdigit():
            return self._resolve_club_record(int(q))
        exact = None
        partial = None
        for club in cidx.clubs:
            for candidate in (club.name, club.short_name):
                if candidate:
                    cl = candidate.lower()
                    if cl == q:
                        exact = club
                        break
                    if partial is None and q in cl:
                        partial = club
            if exact is not None:
                break
        target = exact if exact is not None else partial
        if target is None:
            raise KeyError(f"No club matching {club_uid_or_name!r} found")
        return target

    # ------------------------------------------------------------------
    # 1. Save Metadata, Clock & Human Manager (`game_info`, `save_game_summary`, `humans`)
    # ------------------------------------------------------------------
    def set_save_name(self, new_save_name: str) -> dict[str, Any]:
        """Update the save name stored in the container trailer directory."""
        old_name = self._trailer.save_name
        self._trailer.save_name = new_save_name
        rec = {"type": "set_save_name", "old": old_name, "new": new_save_name}
        self._edit_log.append(rec)
        return rec

    def set_game_date(
        self,
        new_date: datetime.date | str,
        time_slot: int | None = None,
    ) -> dict[str, Any]:
        """Update the save's in-game clock in both `save_game_summary.dat` and `game_info.dat`."""
        target_date = _coerce_date(new_date)
        if target_date is None:
            raise ValueError("new_date cannot be None")

        # 1. Update save_game_summary.dat
        summary_buf = self.get_section_buffer(SAVE_SUMMARY_SECTION)
        summary_schema = read_u16(summary_buf, SCHEMA_OFFSET)
        summary_layout = self._layout(SaveSummaryLayout, SAVE_SUMMARY_SECTION, summary_schema)
        version = find_game_version(summary_buf, summary_layout, self.source_path.name)

        _, offset = read_length_prefixed_string(
            summary_buf, summary_layout.structured_strings_offset, summary_layout.max_setup_string_bytes
        )
        stored_ver, offset = read_length_prefixed_string(
            summary_buf, offset, summary_layout.max_version_bytes
        )
        summary_clock_updated = False
        if stored_ver == version.build:
            div_count = read_u32(summary_buf, offset)
            offset += LENGTH_PREFIX_BYTES
            for _ in range(div_count):
                _, offset = read_length_prefixed_string(
                    summary_buf, offset, summary_layout.max_summary_name_bytes
                )
            _, offset = read_length_prefixed_string(
                summary_buf, offset + summary_layout.manager_header_bytes, summary_layout.max_summary_name_bytes
            )
            _, offset = read_length_prefixed_string(
                summary_buf, offset, summary_layout.max_summary_name_bytes
            )
            clock_at = offset + summary_layout.club_uid_bytes
            write_packed_date_into(summary_buf, clock_at, target_date, time_slot=time_slot)
            summary_clock_updated = True

        # 2. Update game_info.dat
        info_buf = self.get_section_buffer(GAME_INFO_SECTION)
        info_schema = read_u16(info_buf, SCHEMA_OFFSET)
        info_layout = self._layout(GameInfoLayout, GAME_INFO_SECTION, info_schema)
        _, ver_end = read_length_prefixed_string(
            info_buf, info_layout.db_version_length_offset, info_layout.max_db_version_bytes
        )
        var_bytes = game_info_filename_bytes(info_buf, info_layout, ver_end)
        info_date_offset = ver_end + var_bytes + info_layout.game_date_offset_after_db_version
        write_packed_date_into(info_buf, info_date_offset, target_date, time_slot=time_slot)

        rec = {
            "type": "set_game_date",
            "new_date": str(target_date),
            "time_slot": time_slot,
            "summary_clock_updated": summary_clock_updated,
        }
        self._edit_log.append(rec)
        return rec

    def set_human_manager(
        self,
        *,
        person_selector: int | None = None,
        club_uid: int | None = None,
    ) -> dict[str, Any]:
        """Update the human manager's person selector in `humans.dat` and/or managed club UID in `save_game_summary.dat`."""
        changes: dict[str, Any] = {"type": "set_human_manager"}
        if person_selector is not None:
            humans_buf = self.get_section_buffer(HUMANS_SECTION)
            humans_layout = self._layout(HumansLayout, HUMANS_SECTION)
            old_sel = read_u32(humans_buf, humans_layout.first_selector_offset)
            struct.pack_into("<I", humans_buf, humans_layout.first_selector_offset, int(person_selector))
            changes["old_selector"] = old_sel
            changes["new_selector"] = int(person_selector)

        if club_uid is not None:
            summary_buf = self.get_section_buffer(SAVE_SUMMARY_SECTION)
            summary_schema = read_u16(summary_buf, SCHEMA_OFFSET)
            summary_layout = self._layout(SaveSummaryLayout, SAVE_SUMMARY_SECTION, summary_schema)
            _, offset = read_length_prefixed_string(
                summary_buf, summary_layout.structured_strings_offset, summary_layout.max_setup_string_bytes
            )
            _, offset = read_length_prefixed_string(
                summary_buf, offset, summary_layout.max_version_bytes
            )
            div_count = read_u32(summary_buf, offset)
            offset += LENGTH_PREFIX_BYTES
            for _ in range(div_count):
                _, offset = read_length_prefixed_string(
                    summary_buf, offset, summary_layout.max_summary_name_bytes
                )
            _, offset = read_length_prefixed_string(
                summary_buf, offset + summary_layout.manager_header_bytes, summary_layout.max_summary_name_bytes
            )
            _, offset = read_length_prefixed_string(
                summary_buf, offset, summary_layout.max_summary_name_bytes
            )
            old_cuid = read_u32(summary_buf, offset)
            struct.pack_into("<I", summary_buf, offset, int(club_uid))
            changes["old_club_uid"] = old_cuid
            changes["new_club_uid"] = int(club_uid)

        self._edit_log.append(changes)
        return changes

    # ------------------------------------------------------------------
    # 2. Players, Persons, Relations & Name Pools (`game_db.dat`)
    # ------------------------------------------------------------------
    def edit_player(
        self,
        player_uid_or_name: int | str,
        *,
        current_ability: int | None = None,
        potential_ability: int | None = None,
        home_reputation: int | None = None,
        current_reputation: int | None = None,
        world_reputation: int | None = None,
        reputation_bucket: int | None = None,
        team_id: int | None = None,
        club_uid: int | str | None = None,
        team_slot: int = 0,
        transfer_value: int | None = None,
        club_join_date: datetime.date | str | None = None,
        condition: int | None = None,
        condition_pct: float | None = None,
        match_sharpness: int | None = None,
        sharpness_pct: float | None = None,
        height_cm: int | None = None,
        squad_number: int | None = None,
        body_type_code: int | None = None,
        left_foot: int | None = None,
        right_foot: int | None = None,
        positions: Mapping[str, int] | None = None,
        attributes: Mapping[str, int] | None = None,
        raw_attribute_scale: bool = False,
        birth_date: datetime.date | str | None = None,
        age: int | None = None,
        nation_id: int | None = None,
        personality: Mapping[str, int] | None = None,
        traits: int | Iterable[PlayerTrait | str] | None = None,
        first_name_id: int | None = None,
        surname_id: int | None = None,
        common_name_id: int | None = None,
        sync_contract_team: bool = True,
    ) -> dict[str, Any]:
        """Modify any decoded or enriched field on a player record and its PersonBlock in `game_db.dat`.

        Args:
            player_uid_or_name: Player UID, pindex (`id`), or name substring.
            current_ability: CA (`0..200`, or up to `255`). Also syncs `rca_peak_byte`.
            potential_ability: PA (`-10..200`, or up to `255`). Also syncs `pa_copy_byte`.
            home_reputation, current_reputation, world_reputation: Reputation (`1..10000`).
            reputation_bucket: Reputation bucket byte (`0..200`).
            team_id: Direct team ID, or specify `club_uid` (and `team_slot=0`) to move player to a club.
            transfer_value: Transfer value in currency (`0..300_000_000`).
            club_join_date: Date joined club (`datetime.date` or `"YYYY-MM-DD"`).
            condition / condition_pct: Raw condition (`0..10000`) or percentage (`0.0..100.0`).
            match_sharpness / sharpness_pct: Raw sharpness (`0..10000`) or percentage (`0.0..100.0`).
            height_cm: Player height in cm (`150..210`).
            squad_number: Shirt number (`1..99`, or `0`/`255` to clear).
            body_type_code: Enriched body type code (`1..5`).
            left_foot, right_foot: Foot rating (`1..20` visible scale, or `1..100` if `raw_attribute_scale=True`).
            positions: Dict of position ratings (`1..20`, e.g. `{"st": 20, "amc": 18}`).
            attributes: Dict of player attributes (52 attributes; `1..20` visible scale by default,
                converted via `val * 5` to `1..100` raw scale unless `raw_attribute_scale=True`).
            birth_date / age: Birth date (`YYYY-MM-DD`) or integer age in years relative to save clock.
            nation_id: Primary nationality ID (`1..999`).
            personality: Dict of personality attributes (`1..20`: `adaptability`, `ambition`, `controversy`,
                `loyalty`, `pressure`, `professionalism`, `sportsmanship`, `temperament`).
            traits: Integer 64-bit mask or iterable of `PlayerTrait` / trait names.
            first_name_id, surname_id, common_name_id: Name pool IDs (`-1` or `0xFFFFFFFF` for None).
        """
        db = self._game_db_buf()
        layout: PlayerRecordLayout = self._layout(PlayerRecordLayout)
        person_layout: PersonBlockLayout = self._layout(PersonBlockLayout)
        prec = self._player_records()
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        next_rec_off = (
            prec.record_offsets[pos_idx + 1]
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )

        modified: dict[str, Any] = {"uid": uid, "record_offset": rec_off}

        # 1. Ability & Reputations
        if current_ability is not None:
            ca_val = max(0, min(255, int(current_ability)))
            struct.pack_into("<H", db, rec_off + layout.current_ability_offset, ca_val)
            # Sync enriched rca_peak_byte if in range 1..200
            if layout.height_offset >= 121 and 1 <= ca_val <= 200:
                db[rec_off + layout.height_offset - 4] = ca_val
            modified["current_ability"] = ca_val

        if potential_ability is not None:
            pa_val = max(-20, min(255, int(potential_ability)))
            struct.pack_into("<h", db, rec_off + layout.potential_ability_offset, pa_val)
            if layout.height_offset >= 121 and 1 <= pa_val <= 200:
                db[rec_off + layout.height_offset - 3] = pa_val
            modified["potential_ability"] = pa_val

        if home_reputation is not None:
            hr = max(1, min(10_000, int(home_reputation)))
            struct.pack_into("<H", db, rec_off + layout.home_reputation_offset, hr)
            modified["home_reputation"] = hr

        if current_reputation is not None:
            cr = max(1, min(10_000, int(current_reputation)))
            struct.pack_into("<H", db, rec_off + layout.current_reputation_offset, cr)
            modified["current_reputation"] = cr

        if world_reputation is not None:
            wr = max(1, min(10_000, int(world_reputation)))
            struct.pack_into("<H", db, rec_off + layout.world_reputation_offset, wr)
            modified["world_reputation"] = wr

        if reputation_bucket is not None:
            rb = max(0, min(200, int(reputation_bucket)))
            db[rec_off + layout.reputation_bucket_offset] = rb
            modified["reputation_bucket"] = rb

        # 2. Club / Team assignment
        resolved_team_id = team_id
        if club_uid is not None:
            club_obj = self._resolve_club_record(club_uid)
            if not club_obj.teams:
                raise ValueError(f"Club {club_obj.name} ({club_obj.uid}) has no teams")
            slot_idx = max(0, min(len(club_obj.teams) - 1, int(team_slot)))
            resolved_team_id = club_obj.teams[slot_idx].team_id

        if resolved_team_id is not None:
            struct.pack_into("<I", db, rec_off + layout.team_id_offset, int(resolved_team_id))
            modified["team_id"] = int(resolved_team_id)
            if sync_contract_team:
                try:
                    self.edit_player_contract(uid, team_id=int(resolved_team_id))
                except Exception:
                    pass

        # 3. Tail Fields (Transfer Value, Join Date, Sharpness, Condition, Height, Enriched Tail)
        if transfer_value is not None:
            tv = max(0, int(transfer_value))
            struct.pack_into("<I", db, rec_off + layout.transfer_value_offset, tv)
            modified["transfer_value"] = tv

        if club_join_date is not None:
            write_packed_date_into(db, rec_off + layout.club_join_date_offset, club_join_date)
            modified["club_join_date"] = str(_coerce_date(club_join_date))

        if condition_pct is not None:
            condition = int(round(float(condition_pct) * 100.0))
        if condition is not None:
            c_val = max(0, min(10_000, int(condition)))
            struct.pack_into("<H", db, rec_off + layout.condition_offset, c_val)
            modified["condition"] = c_val

        if sharpness_pct is not None:
            match_sharpness = int(round(float(sharpness_pct) * 100.0))
        if match_sharpness is not None:
            ms_val = max(0, min(10_000, int(match_sharpness)))
            struct.pack_into("<H", db, rec_off + layout.match_sharpness_offset, ms_val)
            modified["match_sharpness"] = ms_val

        if height_cm is not None:
            h_val = max(150, min(210, int(height_cm)))
            db[rec_off + layout.height_offset] = h_val
            modified["height_cm"] = h_val

        if squad_number is not None and layout.height_offset >= 121:
            sn = 255 if squad_number <= 0 or squad_number > 99 else int(squad_number)
            db[rec_off + layout.height_offset - 5] = sn
            modified["squad_number"] = None if sn == 255 else sn

        if body_type_code is not None:
            bt = max(1, min(10, int(body_type_code)))
            db[rec_off + layout.height_offset + 1] = bt
            modified["body_type_code"] = bt

        # 4. Positional Familiarity Ratings (15 bytes at ratings_offset)
        if positions:
            pos_aliases = {
                "GK": 0, "GOALKEEPER": 0,
                "SW": 1, "SWEEPER": 1,
                "DL": 2, "LEFT_BACK": 2,
                "DC": 3, "CENTRE_BACK": 3, "CB": 3,
                "DR": 4, "RIGHT_BACK": 4,
                "DM": 5, "DEFENSIVE_MIDFIELDER": 5, "DMC": 5,
                "ML": 6, "LEFT_MIDFIELDER": 6,
                "MC": 7, "CENTRAL_MIDFIELDER": 7, "CM": 7,
                "MR": 8, "RIGHT_MIDFIELDER": 8,
                "AML": 9, "ATTACKING_MIDFIELDER_LEFT": 9, "LW": 9,
                "AMC": 10, "ATTACKING_MIDFIELDER_CENTRAL": 10, "CAM": 10,
                "AMR": 11, "ATTACKING_MIDFIELDER_RIGHT": 11, "RW": 11,
                "STC": 12, "ST": 12, "SC": 12, "STRIKER": 12, "CF": 12,
                "WBL": 13, "LEFT_WING_BACK": 13, "LWB": 13,
                "WBR": 14, "RIGHT_WING_BACK": 14, "RWB": 14,
            }
            pos_changes: dict[str, int] = {}
            for k, v in positions.items():
                key_up = k.strip().upper()
                if key_up not in pos_aliases:
                    raise ValueError(f"Unknown position code {k!r}")
                p_idx = pos_aliases[key_up]
                val_20 = max(1, min(20, int(v)))
                db[rec_off + layout.ratings_offset + p_idx] = val_20
                pos_changes[key_up] = val_20
            modified["positions"] = pos_changes

        # 5. Foot Ratings & 52 Attributes (54 bytes at attributes_offset)
        def _to_raw_100(val: int, is_raw: bool) -> int:
            v = int(val)
            if is_raw or v > 20:
                return max(1, min(100, v))
            return max(1, min(100, v * 5))

        if left_foot is not None:
            lf_raw = _to_raw_100(left_foot, raw_attribute_scale)
            db[rec_off + layout.attributes_offset + layout.left_foot_index] = lf_raw
            modified["left_foot_raw"] = lf_raw

        if right_foot is not None:
            rf_raw = _to_raw_100(right_foot, raw_attribute_scale)
            db[rec_off + layout.attributes_offset + layout.right_foot_index] = rf_raw
            modified["right_foot_raw"] = rf_raw

        if attributes:
            # Map attribute_field_order to byte index in the 54-byte span (skipping left_foot_index & right_foot_index)
            skip_indices = {layout.left_foot_index, layout.right_foot_index}
            byte_indices = [i for i in range(layout.attribute_count) if i not in skip_indices]
            attr_to_byte_idx = {
                name: byte_indices[pos]
                for pos, name in enumerate(layout.attribute_field_order)
            }
            attr_changes: dict[str, int] = {}
            for attr_name, attr_val in attributes.items():
                norm_name = attr_name.strip().lower()
                if norm_name == "left_foot":
                    raw_v = _to_raw_100(attr_val, raw_attribute_scale)
                    db[rec_off + layout.attributes_offset + layout.left_foot_index] = raw_v
                    attr_changes["left_foot"] = raw_v
                    continue
                if norm_name == "right_foot":
                    raw_v = _to_raw_100(attr_val, raw_attribute_scale)
                    db[rec_off + layout.attributes_offset + layout.right_foot_index] = raw_v
                    attr_changes["right_foot"] = raw_v
                    continue
                if norm_name not in attr_to_byte_idx:
                    raise ValueError(
                        f"Unknown player attribute {attr_name!r}. Valid attributes: {layout.attribute_field_order}"
                    )
                b_idx = attr_to_byte_idx[norm_name]
                raw_v = _to_raw_100(attr_val, raw_attribute_scale)
                db[rec_off + layout.attributes_offset + b_idx] = raw_v
                attr_changes[norm_name] = raw_v
            modified["attributes_raw"] = attr_changes

        # 6. PersonBlock Fields (Birth Date / Age, Nation, Personality, Traits, Name IDs)
        needs_person_block = any(
            x is not None
            for x in (
                birth_date,
                age,
                nation_id,
                personality,
                traits,
                first_name_id,
                surname_id,
                common_name_id,
            )
        )
        if needs_person_block:
            clock_yr = (self.get_game_date() or datetime.date(2050, 1, 1)).year
            pblock = locate_person_block(
                db,
                rec_off + person_layout.window_start_offset,
                next_rec_off,
                person_layout,
                clock_year=clock_yr,
            )
            if pblock is None:
                raise RuntimeError(f"Could not locate PersonBlock for player {uid} at {rec_off}")
            b_off = pblock.birth_date_offset

            if age is not None and birth_date is None:
                clock = self._save_reader.info.game_date or datetime.date(2025, 8, 1)
                existing_bd = decode_date(db, b_off) or datetime.date(clock.year - int(age), 6, 15)
                target_year = clock.year - int(age)
                try:
                    birth_date = existing_bd.replace(year=target_year)
                except ValueError:
                    birth_date = datetime.date(target_year, existing_bd.month, 28)

            if birth_date is not None:
                write_packed_date_into(db, b_off, birth_date)
                modified["birth_date"] = str(_coerce_date(birth_date))

            if nation_id is not None:
                nat_val = max(1, min(65535, int(nation_id)))
                struct.pack_into("<H", db, b_off + person_layout.nation_id_offset_from_birth, nat_val)
                modified["nation_id"] = nat_val

            if personality:
                pers_order = (
                    "adaptability",
                    "ambition",
                    "controversy",
                    "loyalty",
                    "pressure",
                    "professionalism",
                    "sportsmanship",
                    "temperament",
                )
                pers_base = b_off + person_layout.personality_offset_from_birth
                pers_changes: dict[str, int] = {}
                for pk, pv in personality.items():
                    pk_norm = pk.strip().lower()
                    if pk_norm not in pers_order:
                        raise ValueError(f"Unknown personality field {pk!r}. Valid: {pers_order}")
                    p_idx = pers_order.index(pk_norm)
                    p_val = max(1, min(20, int(pv)))
                    db[pers_base + p_idx] = p_val
                    pers_changes[pk_norm] = p_val
                modified["personality"] = pers_changes

            if pblock.has_name_block:
                nb_off = b_off + pblock.name_block_offset_from_birth
                if traits is not None:
                    if isinstance(traits, int):
                        mask = traits & 0xFFFFFFFFFFFFFFFF
                    else:
                        mask = 0
                        for t in traits:
                            if isinstance(t, PlayerTrait):
                                mask |= int(t)
                            else:
                                t_name = str(t).strip().upper()
                                mask |= int(PlayerTrait[t_name])
                    struct.pack_into(
                        "<Q",
                        db,
                        nb_off + person_layout.trait_bits_offset_from_block_start,
                        mask,
                    )
                    modified["trait_bits"] = mask

                if first_name_id is not None:
                    fn_val = MISSING_REFERENCE if first_name_id < 0 else int(first_name_id)
                    struct.pack_into(
                        "<I",
                        db,
                        nb_off + person_layout.first_name_id_offset_from_block_start,
                        fn_val,
                    )
                    modified["first_name_id"] = fn_val

                if surname_id is not None:
                    sn_val = MISSING_REFERENCE if surname_id < 0 else int(surname_id)
                    struct.pack_into(
                        "<I",
                        db,
                        nb_off + person_layout.surname_id_offset_from_block_start,
                        sn_val,
                    )
                    modified["surname_id"] = sn_val

                if common_name_id is not None:
                    cn_val = MISSING_REFERENCE if common_name_id < 0 else int(common_name_id)
                    struct.pack_into(
                        "<I",
                        db,
                        nb_off + person_layout.common_name_id_offset_from_block_start,
                        cn_val,
                    )
                    modified["common_name_id"] = cn_val

        self._edit_log.append({"type": "edit_player", **modified})
        return modified

    def max_out_player(
        self,
        player_uid_or_name: int | str,
        *,
        ca: int = 200,
        pa: int = 200,
        attribute_value: int = 20,
        reputation: int = 10_000,
        include_gk_for_outfield: bool = False,
    ) -> dict[str, Any]:
        """Maximize a player's CA/PA (200/200), attributes (20), reputation (10000), condition/sharpness (100%),
        and positive personality/hidden traits while minimizing negative hidden traits (`injury_proneness=1`,
        `dirtiness=1`, `controversy=1`).

        Preserves outfield players' low goalkeeping attributes by default so `_core` population gate
        checks (`handling_above_finishing` and `outfield_goalkeeper_block_low`) always pass.
        """
        db = self._game_db_buf()
        layout: PlayerRecordLayout = self._layout(PlayerRecordLayout)
        _pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)

        gk_rating = db[rec_off + layout.ratings_offset + 0]
        is_gk = gk_rating >= 15
        gk_attrs = {
            "handling", "aerial_reach", "command_of_area", "communication",
            "kicking", "throwing", "one_on_ones", "reflexes", "rushing_out",
            "punching", "eccentricity",
        }
        negative_attrs = {"dirtiness", "injury_proneness"}

        attrs_to_set: dict[str, int] = {}
        for attr_name in layout.attribute_field_order:
            if attr_name in negative_attrs:
                attrs_to_set[attr_name] = 1
            elif attr_name in gk_attrs:
                if is_gk or include_gk_for_outfield:
                    attrs_to_set[attr_name] = 1 if attr_name == "eccentricity" else attribute_value
            else:
                attrs_to_set[attr_name] = attribute_value

        personality_to_set = {
            "adaptability": 20,
            "ambition": 20,
            "controversy": 1,
            "loyalty": 20,
            "pressure": 20,
            "professionalism": 20,
            "sportsmanship": 20,
            "temperament": 20,
        }

        return self.edit_player(
            uid,
            current_ability=ca,
            potential_ability=pa,
            home_reputation=reputation,
            current_reputation=reputation,
            world_reputation=reputation,
            condition=10_000,
            match_sharpness=10_000,
            left_foot=20,
            right_foot=20,
            attributes=attrs_to_set,
            personality=personality_to_set,
        )

    def edit_player_relation_entry(
        self,
        player_uid_or_name: int | str,
        entry_index: int,
        *,
        referenced_id: int | None = None,
        kind: int | None = None,
        role: int | None = None,
        qualifier: int | None = None,
    ) -> dict[str, Any]:
        """Edit one of the 16-byte relation entries (`second_nation_ids`, `home_grown_club_uids`,
        `favoured_clubs`, `languages`, etc.) in a player's `PersonBlock`.
        """
        db = self._game_db_buf()
        person_layout: PersonBlockLayout = self._layout(PersonBlockLayout)
        prec = self._player_records()
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        next_rec_off = (
            prec.record_offsets[pos_idx + 1]
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )
        clock_yr = (self.get_game_date() or datetime.date(2050, 1, 1)).year
        pblock = locate_person_block(
            db,
            rec_off + person_layout.window_start_offset,
            next_rec_off,
            person_layout,
            clock_year=clock_yr,
        )
        if pblock is None:
            raise RuntimeError(f"Could not locate PersonBlock for player {uid}")
        b_off = pblock.birth_date_offset
        if db[b_off + person_layout.relation_present_offset_from_birth] == 0:
            raise ValueError(f"Player {uid} has no relation block present")
        rel_count = db[b_off + person_layout.relation_count_offset_from_birth]
        if not 0 <= entry_index < rel_count:
            raise IndexError(f"Relation entry index {entry_index} out of range (0..{rel_count - 1})")
        entry_off = (
            b_off
            + person_layout.relation_entries_offset_from_birth
            + entry_index * person_layout.relation_entry_bytes
        )
        if referenced_id is not None:
            struct.pack_into(
                "<I",
                db,
                entry_off + person_layout.relation_referenced_offset_in_entry,
                int(referenced_id),
            )
        if kind is not None:
            db[entry_off + person_layout.relation_kind_role_offset_in_entry] = int(kind) & 0xFF
        if role is not None:
            db[entry_off + person_layout.relation_kind_role_offset_in_entry + 1] = int(role) & 0xFF
        if qualifier is not None:
            db[entry_off + person_layout.relation_qualifier_offset_in_entry] = int(qualifier) & 0xFF
        db[entry_off + person_layout.relation_sentinel_offset_in_entry] = (
            person_layout.relation_sentinel_value
        )
        rec = {
            "type": "edit_player_relation_entry",
            "uid": uid,
            "entry_index": entry_index,
            "referenced_id": referenced_id,
            "kind": kind,
            "role": role,
            "qualifier": qualifier,
        }
        self._edit_log.append(rec)
        return rec

    def rename_name_pool_entry(
        self,
        pool_kind: str,
        name_id: int,
        new_name: str,
    ) -> dict[str, Any]:
        """Update a name string inside one of the three `game_db.dat` name pools
        (`"first_names"`, `"surnames"`, or `"common_names"`).

        If `new_name` has the exact same UTF-8 byte length, patches in place; otherwise
        splices the updated length-prefixed UTF-8 string into the pool and invalidates cached offsets.
        """
        db = self._game_db_buf()
        pool_layout: NamePoolLayout = self._layout(NamePoolLayout)
        offsets = locate_name_pools(db, pool_layout, self.source_path.name)
        if offsets is None:
            raise RuntimeError("Could not locate name pools in game_db")
        kind_norm = pool_kind.strip().lower()
        if kind_norm in ("first", "first_name", "first_names"):
            pool = offsets.first_names
        elif kind_norm in ("surname", "surnames", "last", "last_name"):
            pool = offsets.surnames
        elif kind_norm in ("common", "common_name", "common_names"):
            pool = offsets.common_names
        else:
            raise ValueError(f"Unknown pool_kind {pool_kind!r}; expected first_names, surnames, or common_names")

        if not 0 <= name_id < pool.entry_count:
            raise KeyError(f"Name ID {name_id} out of range (0..{pool.entry_count - 1}) in pool {pool_kind!r}")
        cursor = pool.entry_offsets[name_id]
        str_len = read_u32(db, cursor)
        str_start = cursor + 4
        str_end = str_start + str_len
        old_text = db[str_start:str_end].decode("utf-8", errors="replace")
        new_bytes = new_name.encode("utf-8")
        struct.pack_into("<I", db, cursor, len(new_bytes))
        db[str_start:str_end] = new_bytes
        self._invalidate_db_caches()
        rec = {
            "type": "rename_name_pool_entry",
            "pool": kind_norm,
            "name_id": name_id,
            "old_name": old_text,
            "new_name": new_name,
        }
        self._edit_log.append(rec)
        return rec

    # ------------------------------------------------------------------
    # 3. Contracts & Clauses (`contracts` + `enrichment` in `game_db.dat`)
    # ------------------------------------------------------------------
    def edit_player_contract(
        self,
        player_uid_or_name: int | str,
        *,
        wage: int | None = None,
        start_date: datetime.date | str | None = None,
        end_date: datetime.date | str | None = None,
        team_id: int | None = None,
        squad_status: int | None = None,
        contract_type: int | None = None,
        signing_or_loyalty_fee: int | None = None,
        agent_fee: int | None = None,
        package_bonus: int | None = None,
        option_or_reference_year: int | None = None,
        clause_updates: Sequence[Mapping[str, int]] | None = None,
    ) -> dict[str, Any]:
        """Modify a player's active contract record (including head fees, tail fields, and clauses) in `game_db.dat`.

        Args:
            player_uid_or_name: Player UID, pindex, or name.
            wage: Weekly wage (`<I`).
            start_date: Contract start date (`YYYY-MM-DD`).
            end_date: Contract expiry date (`YYYY-MM-DD`).
            team_id: Contracted team ID (`<I`).
            squad_status: Squad status code (`0..15`, e.g. `1` = Key Player / Star, `2` = Regular Starter).
            contract_type: Head contract type byte (`<B`).
            signing_or_loyalty_fee: `money_a` (`<I`).
            agent_fee: `money_b` (`<I`).
            package_bonus: `money_c` (`<I`).
            option_or_reference_year: `e12` (`<I`).
            clause_updates: Sequence of `{"index": idx, "value": val, "parameter": param, "kind": kind}`.
        """
        db = self._game_db_buf()
        contract_layout: ContractLayout = self._layout(ContractLayout)
        clock = self.get_game_date() or datetime.date(2025, 7, 1)
        decoder = build_contract_decoder(
            contract_layout, self._club_index(), clock, self.source_path.name
        )
        prec = self._player_records()
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        pindex = prec.pindexes[pos_idx]
        next_rec_off = (
            prec.record_offsets[pos_idx + 1]
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )
        found = decoder._find_chain_records(
            db, rec_off, next_rec_off, pos_idx + 1 == len(prec.record_offsets), pindex
        )
        if found is None:
            # Check if player has fallback contract dates inside the player record window
            search_start = rec_off + contract_layout.fallback_start_from_record
            limit = max(search_start, next_rec_off - contract_layout.fallback_end_margin)
            find_end = min(len(db), limit)
            zero_needle = bytes(contract_layout.fallback_nonzero_length)
            hit = db.find(b"\xff\xff\xff\xff", search_start, find_end)
            fallback_updated = []
            while hit >= 0:
                dates_off = hit + 8
                nz_start = dates_off + contract_layout.fallback_nonzero_offset
                if (
                    dates_off + contract_layout.fallback_gate_length <= limit
                    and nz_start + contract_layout.fallback_nonzero_length <= len(db)
                    and db[nz_start : nz_start + contract_layout.fallback_nonzero_length] != zero_needle
                ):
                    ed_off = dates_off + contract_layout.fallback_end_date_offset
                    sd_off = dates_off + contract_layout.fallback_start_date_offset
                    if decode_date(db, ed_off) is not None and decode_date(db, sd_off) is not None:
                        if start_date is not None:
                            write_packed_date_into(db, sd_off, start_date)
                        if end_date is not None:
                            write_packed_date_into(db, ed_off, end_date)
                        fallback_updated.append({"dates_offset": dates_off, "fallback": True})
                hit = db.find(b"\xff\xff\xff\xff", hit + 1, find_end)
            if fallback_updated:
                rec = {"type": "edit_player_contract", "uid": uid, "records": fallback_updated}
                self._edit_log.append(rec)
                return rec
            raise KeyError(f"No contract chain records found for player {uid}")
        chain_hits, _chain_records_list = found

        changes_per_hit: list[dict[str, Any]] = []
        for m_off in chain_hits:
            hit_change: dict[str, Any] = {"tag_offset": m_off}
            if wage is not None:
                struct.pack_into("<I", db, m_off + contract_layout.wage_offset, max(0, int(wage)))
                hit_change["wage"] = int(wage)
            if team_id is not None:
                struct.pack_into("<I", db, m_off + contract_layout.team_id_offset, int(team_id))
                hit_change["team_id"] = int(team_id)
            if start_date is not None:
                write_packed_date_into(db, m_off + contract_layout.start_offset, start_date)
                hit_change["start_date"] = str(_coerce_date(start_date))

            tail_e = decoder._locate_tail(db, m_off)
            if tail_e is not None:
                if end_date is not None:
                    write_packed_date_into(db, tail_e + contract_layout.tail_end_offset, end_date)
                    hit_change["end_date"] = str(_coerce_date(end_date))
                if start_date is not None:
                    if decode_date(db, tail_e + contract_layout.tail_printed_start_offset) is not None:
                        write_packed_date_into(
                            db, tail_e + contract_layout.tail_printed_start_offset, start_date
                        )
                if squad_status is not None:
                    db[tail_e + contract_layout.tail_squad_status_offset] = int(squad_status) & 0xFF
                    hit_change["squad_status"] = int(squad_status)
                if option_or_reference_year is not None:
                    struct.pack_into(
                        "<I",
                        db,
                        tail_e + contract_layout.tail_e12_offset,
                        int(option_or_reference_year),
                    )
                    hit_change["option_or_reference_year"] = int(option_or_reference_year)

                cbase_pair = decoder._locate_clause_base(db, tail_e)
                if cbase_pair is None:
                    cbase_pair = decoder._locate_clause_base_fallback(db, tail_e)
                clause_base = cbase_pair[0] if cbase_pair is not None else None

                if clause_base is not None:
                    # Head fields
                    head_gate_at = clause_base + contract_layout.head_gate_offset
                    if head_gate_at >= 0 and read_u16(db, head_gate_at) == contract_layout.head_gate_value:
                        if contract_type is not None:
                            db[clause_base + contract_layout.head_type_offset] = int(contract_type) & 0xFF
                            hit_change["contract_type"] = int(contract_type)
                        if signing_or_loyalty_fee is not None:
                            struct.pack_into(
                                "<I",
                                db,
                                clause_base + contract_layout.head_money_a_offset,
                                max(0, int(signing_or_loyalty_fee)),
                            )
                            hit_change["signing_or_loyalty_fee"] = int(signing_or_loyalty_fee)
                        if agent_fee is not None:
                            struct.pack_into(
                                "<I",
                                db,
                                clause_base + contract_layout.head_money_b_offset,
                                max(0, int(agent_fee)),
                            )
                            hit_change["agent_fee"] = int(agent_fee)
                        if package_bonus is not None:
                            struct.pack_into(
                                "<I",
                                db,
                                clause_base + contract_layout.head_money_c_offset,
                                max(0, int(package_bonus)),
                            )
                            hit_change["package_bonus"] = int(package_bonus)

                    # Clause updates
                    if clause_updates:
                        c_count = db[clause_base + contract_layout.clause_count_offset]
                        entries_start = clause_base + contract_layout.clause_entries_offset
                        updated_clauses = []
                        for cupd in clause_updates:
                            c_idx = int(cupd.get("index", 0))
                            if 0 <= c_idx < c_count:
                                c_off = entries_start + c_idx * contract_layout.clause_entry_bytes
                                if "value" in cupd:
                                    struct.pack_into(
                                        "<I",
                                        db,
                                        c_off + contract_layout.clause_value_offset,
                                        int(cupd["value"]),
                                    )
                                if "parameter" in cupd:
                                    struct.pack_into(
                                        "<H",
                                        db,
                                        c_off + contract_layout.clause_parameter_offset,
                                        int(cupd["parameter"]),
                                    )
                                if "kind" in cupd:
                                    struct.pack_into(
                                        "<H",
                                        db,
                                        c_off + contract_layout.clause_kind_offset,
                                        int(cupd["kind"]),
                                    )
                                updated_clauses.append(dict(cupd))
                        hit_change["clauses_updated"] = updated_clauses
            elif end_date is not None:
                # Fallback loan/non-tail block
                for ev_cnt in range(contract_layout.loan_block_max_event_count + 1):
                    cand_e = (
                        m_off
                        - contract_layout.tail_base_offset
                        - contract_layout.tail_step_bytes * ev_cnt
                    )
                    if cand_e < 0 or cand_e + decoder.tail_struct.size > len(db):
                        continue
                    if db[cand_e + contract_layout.tail_event_count_offset] == ev_cnt:
                        if decode_date(db, cand_e + contract_layout.tail_end_offset) is not None:
                            write_packed_date_into(
                                db, cand_e + contract_layout.tail_end_offset, end_date
                            )
                            hit_change["end_date"] = str(_coerce_date(end_date))
                            break

            changes_per_hit.append(hit_change)

        rec = {"type": "edit_player_contract", "uid": uid, "records": changes_per_hit}
        self._edit_log.append(rec)
        return rec

    # ------------------------------------------------------------------
    # 4. Suspensions & Injuries (`game_db.dat`, `injury_manager.dat`, `.apm`/`.scm`)
    # ------------------------------------------------------------------
    def edit_player_suspensions(
        self,
        player_uid_or_name: int | str,
        *,
        clear: bool = False,
        issued_date: datetime.date | str | None = None,
        scope_code: int | None = None,
        scope_id: int | None = None,
        e7: int | None = None,
    ) -> dict[str, Any]:
        """Modify or clear unserved suspension entries belonging to a player in `game_db.dat`."""
        db = self._game_db_buf()
        susp_layout: SuspensionLayout = self._layout(SuspensionLayout)
        prec = self._player_records()
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        win_start = max(0, rec_off - susp_layout.owner_back_offset)
        win_end = (
            prec.record_offsets[pos_idx + 1] - susp_layout.owner_back_offset
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )

        # Find standalone and parent-attached suspension entries inside [win_start, win_end)
        entry_offsets: list[tuple[int, str]] = []
        sig = susp_layout.signature
        core_bytes = susp_layout.entry_core_bytes
        null_sfx = susp_layout.null_suffix

        cursor = win_start
        while cursor + core_bytes + len(null_sfx) <= win_end:
            if all(db[cursor + off] == val for off, val in sig):
                if db[cursor + core_bytes : cursor + core_bytes + len(null_sfx)] == null_sfx:
                    if decode_date(db, cursor + susp_layout.issued_date_offset) is not None:
                        entry_offsets.append((cursor, "standalone"))
                        cursor += core_bytes + len(null_sfx)
                        continue
            # Also check parent-attached list starting with parent_prefix (01 00 <count>)
            if (
                db[cursor : cursor + len(susp_layout.parent_prefix)] == susp_layout.parent_prefix
                and cursor + 3 <= win_end
            ):
                child_count = db[cursor + len(susp_layout.parent_prefix)]
                if 1 <= child_count <= 16:
                    c_pos = cursor + len(susp_layout.parent_prefix) + 1
                    temp_children: list[int] = []
                    valid_parent = True
                    for _ in range(child_count):
                        if c_pos + core_bytes > win_end or not all(
                            db[c_pos + off] == val for off, val in sig
                        ):
                            valid_parent = False
                            break
                        if decode_date(db, c_pos + susp_layout.issued_date_offset) is None:
                            valid_parent = False
                            break
                        if db[c_pos + core_bytes : c_pos + core_bytes + len(null_sfx)] == null_sfx:
                            temp_children.append(c_pos)
                            c_pos += core_bytes + len(null_sfx)
                        elif (
                            c_pos + susp_layout.linked_entry_bytes <= win_end
                            and all(
                                db[c_pos + off] == val for off, val in susp_layout.linked_signature
                            )
                        ):
                            temp_children.append(c_pos)
                            c_pos += susp_layout.linked_entry_bytes
                        else:
                            valid_parent = False
                            break
                    if valid_parent:
                        for ch_off in temp_children:
                            entry_offsets.append((ch_off, "attached"))
                        cursor = c_pos
                        continue
            cursor += 1

        modified_entries: list[dict[str, Any]] = []
        for e_off, kind_label in entry_offsets:
            if clear:
                if kind_label == "standalone":
                    # Neutralize signature byte +13 (from 0x05 to 0x00) so standalone ban is inactive
                    db[e_off + 13] = 0x00
                else:
                    # For attached parent-child entries, zero out the issued date to 1900-01-01 (null date)
                    # so decode_date returns None and the ban is no longer active
                    db[
                        e_off + susp_layout.issued_date_offset : e_off
                        + susp_layout.issued_date_offset
                        + 4
                    ] = NULL_DATE_BYTES
                modified_entries.append({"offset": e_off, "kind": kind_label, "cleared": True})
                continue

            if issued_date is not None:
                write_packed_date_into(db, e_off + susp_layout.issued_date_offset, issued_date)
            if scope_code is not None:
                db[e_off + susp_layout.scope_code_offset] = int(scope_code) & 0xFF
            if scope_id is not None:
                struct.pack_into("<H", db, e_off + susp_layout.scope_id_offset, int(scope_id) & 0xFFFF)
            if e7 is not None:
                struct.pack_into("<H", db, e_off + susp_layout.unknown_e7_offset, int(e7) & 0xFFFF)
            modified_entries.append(
                {
                    "offset": e_off,
                    "kind": kind_label,
                    "issued_date": str(_coerce_date(issued_date)) if issued_date else None,
                    "scope_code": scope_code,
                    "scope_id": scope_id,
                    "e7": e7,
                }
            )

        rec = {
            "type": "edit_player_suspensions",
            "uid": uid,
            "entries_modified": len(modified_entries),
            "details": modified_entries,
        }
        self._edit_log.append(rec)
        return rec

    def heal_player_injuries(
        self,
        player_uid_or_name: int | str,
        *,
        restore_condition_and_sharpness: bool = True,
        remove_history_log: bool = False,
    ) -> dict[str, Any]:
        """Remove a player's active injuries from `injury_manager.dat` (and optionally restore
        100% condition and match sharpness in `game_db.dat`).
        """
        prec = self._player_records()
        pos_idx, _rec_off, uid = self._resolve_player_position(player_uid_or_name)
        target_selector = prec.pindexes[pos_idx] + 1

        inj_buf = self.get_section_buffer(INJURY_MANAGER_SECTION)
        inj_layout: InjuryManagerLayout = self._layout(
            InjuryManagerLayout, INJURY_MANAGER_SECTION
        )

        # Parse the 4 arrays and 3 lists in injury_manager.dat
        cursor = inj_layout.arrays_offset
        new_parts: list[bytes] = [bytes(inj_buf[:cursor])]
        removed_counts = [0, 0, 0, 0]

        for arr_idx, stride in enumerate(inj_layout.array_strides):
            row_count = read_u32(inj_buf, cursor)
            cursor += 4
            arr_end = cursor + row_count * stride
            kept_rows: list[bytes] = []
            for r_off in range(cursor, arr_end, stride):
                row_bytes = bytes(inj_buf[r_off : r_off + stride])
                if arr_idx in (0, 1):
                    # Arrays 0 & 1 (stride 14): selector is u32 at offset +9
                    sel = read_u32(row_bytes, 9)
                else:
                    # Arrays 2 (TYPED, stride 13) & 3 (HISTORY, stride 15): selector is u32 at layout.selector_offset (+5)
                    sel = read_u32(row_bytes, inj_layout.selector_offset)
                should_drop = (sel == target_selector) and (
                    arr_idx != inj_layout.log_array_index or remove_history_log
                )
                if should_drop:
                    removed_counts[arr_idx] += 1
                else:
                    kept_rows.append(row_bytes)
            new_parts.append(struct.pack("<I", len(kept_rows)))
            new_parts.extend(kept_rows)
            cursor = arr_end

        for list_idx, entry_bytes in enumerate(inj_layout.list_entry_bytes):
            entry_count = read_u32(inj_buf, cursor)
            cursor += 4
            list_end = cursor + entry_count * entry_bytes
            kept_items: list[bytes] = []
            for l_off in range(cursor, list_end, entry_bytes):
                item_bytes = bytes(inj_buf[l_off : l_off + entry_bytes])
                sel = read_u32(item_bytes, 0)
                if sel == target_selector:
                    continue
                kept_items.append(item_bytes)
            new_parts.append(struct.pack("<I", len(kept_items)))
            new_parts.extend(kept_items)
            cursor = list_end

        new_parts.append(bytes(inj_buf[cursor:]))
        rebuilt = b"".join(new_parts)
        inj_buf[:] = rebuilt

        if restore_condition_and_sharpness:
            self.edit_player(uid, condition=10_000, match_sharpness=10_000)

        rec = {
            "type": "heal_player_injuries",
            "uid": uid,
            "selector": target_selector,
            "removed_by_array": removed_counts,
            "restored_condition": restore_condition_and_sharpness,
        }
        self._edit_log.append(rec)
        return rec

    def edit_injury_row(
        self,
        player_uid_or_name: int | str,
        *,
        date: datetime.date | str | None = None,
        injury_type_id: int | None = None,
        cause_code: int | None = None,
        severity_code: int | None = None,
        r11: int | None = None,
        r12: int | None = None,
    ) -> dict[str, Any]:
        """Edit existing `TYPED` or `HISTORY` injury rows for a player in `injury_manager.dat`."""
        prec = self._player_records()
        pos_idx, _rec_off, uid = self._resolve_player_position(player_uid_or_name)
        target_selector = prec.pindexes[pos_idx] + 1

        inj_buf = self.get_section_buffer(INJURY_MANAGER_SECTION)
        inj_layout: InjuryManagerLayout = self._layout(
            InjuryManagerLayout, INJURY_MANAGER_SECTION
        )

        cursor = inj_layout.arrays_offset
        typed_updated = 0
        log_updated = 0
        for arr_idx, stride in enumerate(inj_layout.array_strides):
            row_count = read_u32(inj_buf, cursor)
            cursor += 4
            arr_end = cursor + row_count * stride
            if arr_idx == inj_layout.typed_array_index:
                for r_off in range(cursor, arr_end, stride):
                    if read_u32(inj_buf, r_off + inj_layout.selector_offset) == target_selector:
                        if date is not None:
                            write_packed_date_into(inj_buf, r_off + inj_layout.date_offset, date)
                        if injury_type_id is not None:
                            struct.pack_into(
                                "<H",
                                inj_buf,
                                r_off + inj_layout.typed_type_offset,
                                int(injury_type_id) & 0xFFFF,
                            )
                        if r11 is not None:
                            inj_buf[r_off + inj_layout.typed_r11_offset] = int(r11) & 0xFF
                        if r12 is not None:
                            inj_buf[r_off + inj_layout.typed_r12_offset] = int(r12) & 0xFF
                        typed_updated += 1
            elif arr_idx == inj_layout.log_array_index:
                for r_off in range(cursor, arr_end, stride):
                    if read_u32(inj_buf, r_off + inj_layout.selector_offset) == target_selector:
                        if date is not None and injury_type_id is None:
                            write_packed_date_into(inj_buf, r_off + inj_layout.date_offset, date)
                        if cause_code is not None:
                            inj_buf[r_off + inj_layout.log_cause_offset] = int(cause_code) & 0xFF
                        if severity_code is not None:
                            inj_buf[r_off + inj_layout.log_severity_offset] = int(severity_code) & 0xFF
                        log_updated += 1
            cursor = arr_end

        rec = {
            "type": "edit_injury_row",
            "uid": uid,
            "typed_rows_updated": typed_updated,
            "log_rows_updated": log_updated,
        }
        self._edit_log.append(rec)
        return rec

    def edit_injury_type_definition(
        self,
        type_id: int,
        *,
        new_name: str | None = None,
        flag: int | None = None,
        second_id: int | None = None,
    ) -> dict[str, Any]:
        """Edit an injury type definition (`InjuryType`) across the `.apm`/`.scm` match files."""
        inj_type_layout: InjuryTypeTableLayout = self._layout(
            InjuryTypeTableLayout, MATCH_FILE_REGION, None
        )
        updated_files = 0
        for entry in self._trailer.top_entries:
            if entry.extension not in (".apm", ".scm"):
                continue
            buf = self._get_entry_buffer(entry)
            if not buf.startswith(inj_type_layout.payload_prefix):
                continue
            # Scan for injury type row: lead_byte (1) + <H type_id + <I str_len + text + <B flag + <H second_id + 00 00
            target_prefix = bytes([inj_type_layout.lead_byte]) + struct.pack("<H", int(type_id))
            pos = 0
            while (hit := buf.find(target_prefix, pos)) != -1:
                pos = hit + 1
                if hit + inj_type_layout.text_offset > len(buf):
                    continue
                s_len = read_u32(buf, hit + inj_type_layout.length_offset)
                low_len, high_len = inj_type_layout.length_range
                if not low_len <= s_len <= high_len:
                    continue
                s_end = hit + inj_type_layout.text_offset + s_len
                if s_end + inj_type_layout.trailer_bytes > len(buf):
                    continue
                if buf[s_end] not in inj_type_layout.flag_values or read_u16(buf, s_end + 3) != 0:
                    continue
                if flag is not None:
                    buf[s_end] = int(flag) & 0x01
                if second_id is not None:
                    struct.pack_into("<H", buf, s_end + 1, int(second_id) & 0xFFFF)
                if new_name is not None:
                    new_bytes = new_name.encode("utf-8")
                    struct.pack_into("<I", buf, hit + inj_type_layout.length_offset, len(new_bytes))
                    buf[hit + inj_type_layout.text_offset : s_end] = new_bytes
                updated_files += 1
                break
            if updated_files >= inj_type_layout.maximum_entries_tried:
                break

        rec = {
            "type": "edit_injury_type_definition",
            "type_id": type_id,
            "updated_match_files": updated_files,
            "new_name": new_name,
            "flag": flag,
            "second_id": second_id,
        }
        self._edit_log.append(rec)
        return rec

    # ------------------------------------------------------------------
    # 5. Clubs, Finances, Sponsorships, Facilities, Stadiums, Affiliates
    # ------------------------------------------------------------------
    def _find_club_status_hit(self, club_uid: int, club_index: int) -> int | None:
        db = self._game_db_buf()
        status_layout: ClubStatusLayout = self._layout(ClubStatusLayout)
        uid_pair = struct.pack("<II", club_uid - 1, club_uid - 1)
        zero_run = bytes(status_layout.confirmation_zero_bytes)
        pos = 0
        fallback_hit: int | None = None
        while (hit := db.find(uid_pair, pos)) != -1:
            pos = hit + 1
            ordinal_at = hit + status_layout.ordinal_offset
            kind_at = hit + status_layout.kind_offset
            if ordinal_at < 0 or kind_at >= len(db):
                continue
            ordinal = read_u32(db, ordinal_at)
            kind = db[kind_at]
            if 0 < ordinal < status_layout.ordinal_limit and kind == status_layout.normal_kind:
                conf_at = hit + status_layout.confirmation_offset
                if (
                    conf_at >= 0
                    and read_u32(db, conf_at) == club_index - 1
                    and db[conf_at + 4 : conf_at + 4 + len(zero_run)] == zero_run
                ):
                    return hit
                if fallback_hit is None:
                    fallback_hit = hit
        return fallback_hit

    def edit_club(
        self,
        club_uid_or_name: int | str,
        *,
        reputation: int | None = None,
        last_league_position: int | None = None,
        nation_id: int | None = None,
        fa_nation_id: int | None = None,
        city_id: int | None = None,
        name: str | None = None,
        short_name: str | None = None,
    ) -> dict[str, Any]:
        """Modify a club's status (`reputation`, `last_league_position`) and/or header fields
        (`nation_id`, `fa_nation_id`, `city_id`, `name`, `short_name`) in `game_db.dat`.
        """
        db = self._game_db_buf()
        club = self._resolve_club_record(club_uid_or_name)
        span = self._club_span(club.uid)
        rec_start = span.record_start
        club_layout: ClubRecordLayout = self._layout(ClubRecordLayout)
        status_layout: ClubStatusLayout = self._layout(ClubStatusLayout)

        modified: dict[str, Any] = {"uid": club.uid, "record_start": rec_start}

        if reputation is not None or last_league_position is not None:
            status_hit = self._find_club_status_hit(club.uid, self._club_index_for_uid(club.uid))
            if status_hit is None:
                raise RuntimeError(f"Could not locate status table entry for club {club.name} ({club.uid})")
            if reputation is not None:
                rep_val = max(1, min(10_000, int(reputation)))
                struct.pack_into("<H", db, status_hit + status_layout.reputation_offset, rep_val)
                modified["reputation"] = rep_val
            if last_league_position is not None:
                pos_val = max(0, min(255, int(last_league_position)))
                db[status_hit + status_layout.position_offset] = pos_val
                modified["last_league_position"] = pos_val

        if nation_id is not None:
            nat = int(nation_id)
            old_nat = read_u32(db, rec_start + club_layout.nation_offset)
            struct.pack_into("<I", db, rec_start + club_layout.nation_offset, nat)
            if read_u32(db, rec_start + club_layout.nation_copy_offset) == old_nat:
                struct.pack_into("<I", db, rec_start + club_layout.nation_copy_offset, nat)
            modified["nation_id"] = nat

        if fa_nation_id is not None:
            struct.pack_into("<I", db, rec_start + club_layout.fa_nation_offset, int(fa_nation_id))
            modified["fa_nation_id"] = int(fa_nation_id)

        if city_id is not None:
            c_val = MISSING_REFERENCE if city_id < 0 else int(city_id)
            struct.pack_into("<I", db, rec_start + club_layout.city_offset, c_val)
            modified["city_id"] = None if c_val == MISSING_REFERENCE else c_val

        if name is not None or short_name is not None:
            long_off = rec_start + club_layout.long_name_offset
            cur_long, after_long = read_length_prefixed_string(
                db, long_off, club_layout.max_name_bytes
            )
            cur_short, after_short = read_length_prefixed_string(
                db, after_long, club_layout.max_name_bytes
            )
            new_long_bytes = (name if name is not None else cur_long).encode("utf-8")
            new_short_bytes = (short_name if short_name is not None else cur_short).encode("utf-8")
            replacement = (
                struct.pack("<I", len(new_long_bytes))
                + new_long_bytes
                + struct.pack("<I", len(new_short_bytes))
                + new_short_bytes
            )
            db[long_off:after_short] = replacement
            if name is not None:
                modified["name"] = name
            if short_name is not None:
                modified["short_name"] = short_name

        self._invalidate_db_caches()
        self._edit_log.append({"type": "edit_club", **modified})
        return modified

    def edit_club_finances(
        self,
        club_uid_or_name: int | str,
        *,
        balance: int | None = None,
        transfer_budget_allocated: int | None = None,
        transfer_budget_remaining: int | None = None,
        wage_budget_weekly: int | None = None,
        wage_payroll_weekly: int | None = None,
        income_excluding_transfers: int | None = None,
        net_transfers: int | None = None,
        wage_bill: int | None = None,
        expenditure_excluding_transfers: int | None = None,
        total_income: int | None = None,
        total_expenditure: int | None = None,
        month_index: int = -1,
    ) -> dict[str, Any]:
        """Modify a club's monthly finance snapshot row in `game_db.dat` while maintaining
        all reader accounting identities (`net == total_income - total_expenditure`,
        `0 <= expenditure_excluding_transfers <= total_expenditure`, and inter-month
        balance continuity `later.balance == earlier.balance + later.net`).

        Args:
            club_uid_or_name: Club UID, index, or name.
            balance: Club bank balance (`-400_000_000 .. 2_000_000_000`).
            transfer_budget_allocated, transfer_budget_remaining: Transfer budgets (`<i`).
            wage_budget_weekly, wage_payroll_weekly: Weekly wage budget & payroll (`<= 20_000_000`).
            month_index: Which row in the club's finance series to edit (`-1` = latest month).
        """
        db = self._game_db_buf()
        club = self._resolve_club_record(club_uid_or_name)
        span = self._club_span(club.uid)
        fin_layout: FinanceChainLayout = self._layout(FinanceChainLayout)

        located = locate_finance_chain(db, span, fin_layout)
        if located is None or located[1] <= 0:
            raise KeyError(
                f"Club {club.name} ({club.uid}) has no monthly finance chain in this save"
            )
        chain_start, row_count, _chains_found = located

        target_idx = row_count + month_index if month_index < 0 else month_index
        if not 0 <= target_idx < row_count:
            raise IndexError(f"Month index {month_index} out of range (0..{row_count - 1})")

        row_off = chain_start + target_idx * fin_layout.row_bytes
        old_bal = struct.unpack_from("<i", db, row_off + fin_layout.balance_offset)[0]
        old_tot_inc = struct.unpack_from("<i", db, row_off + fin_layout.total_income_offset)[0]
        old_tot_exp = struct.unpack_from("<i", db, row_off + fin_layout.total_expenditure_offset)[0]
        old_inc_ex = struct.unpack_from(
            "<i", db, row_off + fin_layout.income_excluding_transfers_offset
        )[0]
        old_exp_ex = struct.unpack_from(
            "<i", db, row_off + fin_layout.expenditure_excluding_transfers_offset
        )[0]

        modified: dict[str, Any] = {
            "uid": club.uid,
            "club_name": club.name,
            "month_index": target_idx,
            "row_offset": row_off,
        }

        if transfer_budget_allocated is not None:
            v = int(transfer_budget_allocated)
            struct.pack_into("<i", db, row_off + fin_layout.transfer_allocated_offset, v)
            modified["transfer_budget_allocated"] = v
            if transfer_budget_remaining is None:
                struct.pack_into("<i", db, row_off + fin_layout.transfer_remaining_offset, v)
                modified["transfer_budget_remaining"] = v

        if transfer_budget_remaining is not None:
            v = int(transfer_budget_remaining)
            struct.pack_into("<i", db, row_off + fin_layout.transfer_remaining_offset, v)
            modified["transfer_budget_remaining"] = v

        if wage_budget_weekly is not None:
            v = max(0, min(fin_layout.weekly_maximum, int(wage_budget_weekly)))
            struct.pack_into("<i", db, row_off + fin_layout.wage_budget_offset, v)
            modified["wage_budget_weekly"] = v

        if wage_payroll_weekly is not None:
            v = max(0, min(fin_layout.weekly_maximum, int(wage_payroll_weekly)))
            struct.pack_into("<i", db, row_off + fin_layout.wage_payroll_offset, v)
            modified["wage_payroll_weekly"] = v

        if net_transfers is not None:
            v = int(net_transfers)
            struct.pack_into("<i", db, row_off + fin_layout.net_transfers_offset, v)
            modified["net_transfers"] = v

        if wage_bill is not None:
            v = int(wage_bill)
            struct.pack_into("<i", db, row_off + fin_layout.wage_bill_offset, v)
            modified["wage_bill"] = v

        new_tot_inc = int(total_income) if total_income is not None else old_tot_inc
        new_tot_exp = int(total_expenditure) if total_expenditure is not None else old_tot_exp
        new_inc_ex = (
            int(income_excluding_transfers)
            if income_excluding_transfers is not None
            else old_inc_ex
        )
        new_exp_ex = (
            int(expenditure_excluding_transfers)
            if expenditure_excluding_transfers is not None
            else old_exp_ex
        )

        if balance is not None:
            low_b, high_b = fin_layout.balance_range
            new_bal = max(low_b, min(high_b, int(balance)))
            delta_bal = new_bal - old_bal
            # Shift all rows' balances by delta_bal so later.balance == earlier.balance + later.net
            # remains 100% preserved across the entire series!
            for r_i in range(row_count):
                r_o = chain_start + r_i * fin_layout.row_bytes
                cur_b = struct.unpack_from("<i", db, r_o + fin_layout.balance_offset)[0]
                clamped_b = max(low_b, min(high_b, cur_b + delta_bal))
                struct.pack_into("<i", db, r_o + fin_layout.balance_offset, clamped_b)
            struct.pack_into("<i", db, row_off + fin_layout.balance_offset, new_bal)
            modified["balance"] = new_bal

        # Keep expenditure_excluding_transfers within [0, new_tot_exp] and income_excluding_transfers within [0, new_tot_inc]
        if new_tot_exp < 0:
            new_tot_exp = 0
        new_exp_ex = max(0, min(new_tot_exp, new_exp_ex))
        if new_tot_inc < 0:
            new_tot_inc = 0
        new_inc_ex = max(0, min(new_tot_inc, new_inc_ex))
        new_net = new_tot_inc - new_tot_exp

        if any(
            x is not None
            for x in (
                total_income,
                total_expenditure,
                income_excluding_transfers,
                expenditure_excluding_transfers,
            )
        ):
            struct.pack_into("<i", db, row_off + fin_layout.total_income_offset, new_tot_inc)
            struct.pack_into("<i", db, row_off + fin_layout.total_expenditure_offset, new_tot_exp)
            struct.pack_into(
                "<i", db, row_off + fin_layout.income_excluding_transfers_offset, new_inc_ex
            )
            struct.pack_into(
                "<i", db, row_off + fin_layout.expenditure_excluding_transfers_offset, new_exp_ex
            )
            struct.pack_into("<i", db, row_off + fin_layout.net_offset, new_net)
            modified["total_income"] = new_tot_inc
            modified["total_expenditure"] = new_tot_exp
            modified["net"] = new_net

        self._edit_log.append({"type": "edit_club_finances", **modified})
        return modified

    def edit_club_sponsorships(
        self,
        club_uid_or_name: int | str,
        sponsor_index: int = 0,
        *,
        kind: int | None = None,
        start_date: datetime.date | str | None = None,
        end_date: datetime.date | str | None = None,
        total_value: int | None = None,
        annual_value: int | None = None,
        flag10: int | None = None,
        u15: int | None = None,
        b17: int | None = None,
        enum18: int | None = None,
        b19: int | None = None,
    ) -> dict[str, Any]:
        """Modify a sponsorship deal row in a club's sponsor chain in `game_db.dat`."""
        db = self._game_db_buf()
        club = self._resolve_club_record(club_uid_or_name)
        span = self._club_span(club.uid)
        fin_layout: FinanceChainLayout = self._layout(FinanceChainLayout)
        spon_layout: SponsorChainLayout = self._layout(SponsorChainLayout)

        located_fin = locate_finance_chain(db, span, fin_layout)
        if located_fin is None:
            raise KeyError(f"Club {club.name} ({club.uid}) has no finance chain")
        chain_start, row_count, _ = located_fin
        fin_end = chain_start + row_count * fin_layout.row_bytes
        located_spon = locate_sponsor_chain(db, fin_end, span.record_end, spon_layout)
        if located_spon is None or located_spon[1] <= 0:
            raise KeyError(f"Club {club.name} ({club.uid}) has no active sponsorship rows")
        spon_start, spon_count = located_spon

        idx = spon_count + sponsor_index if sponsor_index < 0 else sponsor_index
        if not 0 <= idx < spon_count:
            raise IndexError(f"Sponsor index {sponsor_index} out of range (0..{spon_count - 1})")

        r_off = spon_start + idx * spon_layout.row_bytes
        modified: dict[str, Any] = {
            "uid": club.uid,
            "sponsor_index": idx,
            "row_offset": r_off,
        }
        if kind is not None:
            db[r_off + spon_layout.type_offset] = int(kind) & 0xFF
            modified["kind"] = int(kind)
        if start_date is not None:
            write_packed_date_into(db, r_off + spon_layout.start_offset, start_date)
            modified["start_date"] = str(_coerce_date(start_date))
        if end_date is not None:
            write_packed_date_into(db, r_off + spon_layout.end_offset, end_date)
            modified["end_date"] = str(_coerce_date(end_date))
        if total_value is not None:
            tv = max(0, min(spon_layout.value_maximum, int(total_value)))
            struct.pack_into("<i", db, r_off + spon_layout.total_offset, tv)
            modified["total_value"] = tv
        if annual_value is not None:
            av = max(0, min(spon_layout.value_maximum, int(annual_value)))
            struct.pack_into("<i", db, r_off + spon_layout.annual_offset, av)
            modified["annual_value"] = av
        if flag10 is not None:
            db[r_off + spon_layout.flag10_offset] = min(spon_layout.flag10_maximum, max(0, int(flag10)))
            modified["flag10"] = int(flag10)
        if u15 is not None:
            struct.pack_into("<H", db, r_off + spon_layout.u15_offset, int(u15) & 0xFFFF)
            modified["u15"] = int(u15)
        if b17 is not None:
            db[r_off + spon_layout.b17_offset] = int(b17) & 0xFF
            modified["b17"] = int(b17)
        if enum18 is not None:
            db[r_off + spon_layout.enum18_offset] = int(enum18) & 0xFF
            modified["enum18"] = int(enum18)
        if b19 is not None:
            struct.pack_into("<H", db, r_off + spon_layout.b19_offset, int(b19) & 0xFFFF)
            modified["b19"] = int(b19)

        self._edit_log.append({"type": "edit_club_sponsorships", **modified})
        return modified

    def edit_club_facilities(
        self,
        club_uid_or_name: int | str,
        *,
        corporate_facilities: int | None = None,
        post_finance_int_33: int | None = None,
        post_finance_int_41: int | None = None,
        post_finance_int_45: int | None = None,
        post_finance_byte_49: int | None = None,
    ) -> dict[str, Any]:
        """Modify a club's `corporate_facilities` rating (`1..20`) and enriched post-finance
        attendance/fanbase fields (`+33`, `+41`, `+45`, `+49`) in `game_db.dat`.
        """
        db = self._game_db_buf()
        club = self._resolve_club_record(club_uid_or_name)
        span = self._club_span(club.uid)
        fin_layout: FinanceChainLayout = self._layout(FinanceChainLayout)
        fac_layout: FacilityByteLayout = self._layout(FacilityByteLayout)

        located_fin = locate_finance_chain(db, span, fin_layout)
        if located_fin is None:
            raise KeyError(f"Club {club.name} ({club.uid}) has no finance chain for facility offset")
        chain_start, row_count, _ = located_fin
        chain_end = chain_start + row_count * fin_layout.row_bytes

        modified: dict[str, Any] = {"uid": club.uid, "chain_end": chain_end}
        if corporate_facilities is not None:
            low_f, high_f = fac_layout.value_range
            cf_val = max(low_f, min(high_f, int(corporate_facilities)))
            db[chain_end + fac_layout.offset_after_chain] = cf_val
            modified["corporate_facilities"] = cf_val

        if post_finance_int_33 is not None:
            struct.pack_into("<i", db, chain_end + 33, int(post_finance_int_33))
            modified["post_finance_int_33"] = int(post_finance_int_33)
        if post_finance_int_41 is not None:
            struct.pack_into("<i", db, chain_end + 41, int(post_finance_int_41))
            modified["post_finance_int_41"] = int(post_finance_int_41)
        if post_finance_int_45 is not None:
            struct.pack_into("<i", db, chain_end + 45, int(post_finance_int_45))
            modified["post_finance_int_45"] = int(post_finance_int_45)
        if post_finance_byte_49 is not None:
            db[chain_end + 49] = int(post_finance_byte_49) & 0xFF
            modified["post_finance_byte_49"] = int(post_finance_byte_49)

        self._edit_log.append({"type": "edit_club_facilities", **modified})
        return modified

    def edit_stadium(
        self,
        stadium_uid_or_name_or_club: int | str,
        *,
        capacity: int | None = None,
        all_seater_capacity: int | None = None,
        expansion_capacity: int | None = None,
        owner_club_uid: int | None = None,
        pitch_length_dm: int | None = None,
        pitch_width_dm: int | None = None,
        pitch_min_length_dm: int | None = None,
        pitch_min_width_dm: int | None = None,
        pitch_max_length_dm: int | None = None,
        pitch_max_width_dm: int | None = None,
        built_date: datetime.date | str | None = None,
        rebuilt_date: datetime.date | str | None = None,
        date_58: datetime.date | str | None = None,
        u17: int | None = None,
        u25: int | None = None,
        b33: int | None = None,
        flags_156: int | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Modify a stadium row in the `game_db.dat` stadium table.

        Automatically keeps `all_seater_capacity <= capacity` (so `stadium_capacity_within_all_seater`
        passes: note that in FM26 `capacity` is total capacity and `all_seater` is seated capacity,
        Wait — let's check `stadiums.py` for `capacity_within_all_seater`!).
        """
        db = self._game_db_buf()
        stad_layout: StadiumTableLayout = self._layout(StadiumTableLayout)
        sidx = self._stadium_index()

        # Resolve target stadium row
        cidx = self._club_index()
        target_row = None
        if isinstance(stadium_uid_or_name_or_club, int):
            q_id = stadium_uid_or_name_or_club
            # 1. Exact stadium UID match
            target_row = next((r for r in sidx.rows if r.uid == q_id), None)
            # 2. Club UID match (owner_club_uid or home_club_uids)
            if target_row is None:
                for r in sidx.rows:
                    owner_uid = (
                        cidx.uid_by_club_index.get(r.owner_club_index)
                        if r.owner_club_index is not None
                        else None
                    )
                    if owner_uid == q_id:
                        target_row = r
                        break
            if target_row is None:
                try:
                    for st in self._save_reader.stadiums():
                        if st.uid == q_id or st.owner_club_uid == q_id or q_id in st.home_club_uids:
                            target_row = next((r for r in sidx.rows if r.uid == st.uid), None)
                            if target_row is not None:
                                break
                except Exception:
                    pass
            # 3. Ordinal fallback
            if target_row is None:
                target_row = next((r for r in sidx.rows if r.ordinal == q_id), None)
        else:
            q_str = stadium_uid_or_name_or_club.strip().lower()
            if q_str.isdigit():
                return self.edit_stadium(
                    int(q_str),
                    capacity=capacity,
                    all_seater_capacity=all_seater_capacity,
                    expansion_capacity=expansion_capacity,
                    owner_club_uid=owner_club_uid,
                    pitch_length_dm=pitch_length_dm,
                    pitch_width_dm=pitch_width_dm,
                    pitch_min_length_dm=pitch_min_length_dm,
                    pitch_min_width_dm=pitch_min_width_dm,
                    pitch_max_length_dm=pitch_max_length_dm,
                    pitch_max_width_dm=pitch_max_width_dm,
                    built_date=built_date,
                    rebuilt_date=rebuilt_date,
                    date_58=date_58,
                    u17=u17,
                    u25=u25,
                    b33=b33,
                    flags_156=flags_156,
                    name=name,
                )
            for r in sidx.rows:
                if r.name and q_str in r.name.lower():
                    target_row = r
                    break
            if target_row is None:
                # Try resolving as club name
                try:
                    c_obj = self._resolve_club_record(stadium_uid_or_name_or_club)
                    c_idx_val = self._club_index_for_uid(c_obj.uid)
                    for r in sidx.rows:
                        if r.owner_club_index == c_idx_val:
                            target_row = r
                            break
                except Exception:
                    pass

        if target_row is None:
            raise KeyError(f"Stadium matching {stadium_uid_or_name_or_club!r} not found")

        # Locate exact byte offset of target_row in game_db (stored uid is uid - 1)
        header_sig = struct.pack(
            "<IIIB", target_row.ordinal, target_row.uid - 1, target_row.uid - 1, 0
        )
        row_off = db.find(header_sig)
        if row_off < 0:
            raise RuntimeError(f"Could not locate binary row for stadium UID {target_row.uid}")

        modified: dict[str, Any] = {
            "uid": target_row.uid,
            "ordinal": target_row.ordinal,
            "row_offset": row_off,
        }

        cur_cap = struct.unpack_from("<i", db, row_off + stad_layout.capacity_offset)[0]
        cur_seat = struct.unpack_from("<i", db, row_off + stad_layout.all_seater_offset)[0]
        new_cap = int(capacity) if capacity is not None else cur_cap
        new_seat = int(all_seater_capacity) if all_seater_capacity is not None else cur_seat

        # In stadiums.py: `0 <= capacity <= all_seater` or `all_seater == 0` is what `capacity_within_all_seater`
        # checks! Wait: when `all_seater > 0`, `all_seater` is the ceiling/all-seater capacity and `capacity <= all_seater`!
        if capacity is not None and all_seater_capacity is None and new_seat > 0 and new_cap > new_seat:
            new_seat = new_cap

        if capacity is not None:
            struct.pack_into("<i", db, row_off + stad_layout.capacity_offset, new_cap)
            modified["capacity"] = new_cap
        if all_seater_capacity is not None or new_seat != cur_seat:
            struct.pack_into("<i", db, row_off + stad_layout.all_seater_offset, new_seat)
            modified["all_seater_capacity"] = new_seat
        if expansion_capacity is not None:
            struct.pack_into(
                "<i", db, row_off + stad_layout.expansion_offset, int(expansion_capacity)
            )
            modified["expansion_capacity"] = int(expansion_capacity)
        if owner_club_uid is not None:
            ow = MISSING_REFERENCE if owner_club_uid <= 0 else int(owner_club_uid) - 1
            struct.pack_into("<I", db, row_off + stad_layout.owner_offset, ow)
            modified["owner_club_uid"] = None if ow == MISSING_REFERENCE else ow + 1

        # Pitch dimensions (keep min <= actual <= max and length > width so pitch_within_limits holds)
        cur_len = read_u16(db, row_off + stad_layout.pitch_length_offset)
        cur_wid = read_u16(db, row_off + stad_layout.pitch_width_offset)
        cur_min_l = read_u16(db, row_off + stad_layout.pitch_min_length_offset)
        cur_max_l = read_u16(db, row_off + stad_layout.pitch_max_length_offset)
        cur_min_w = read_u16(db, row_off + stad_layout.pitch_min_width_offset)
        cur_max_w = read_u16(db, row_off + stad_layout.pitch_max_width_offset)

        if pitch_length_dm is not None:
            low_pl, high_pl = stad_layout.pitch_length_range
            pl = max(low_pl, min(high_pl, int(pitch_length_dm)))
            struct.pack_into("<H", db, row_off + stad_layout.pitch_length_offset, pl)
            modified["pitch_length_dm"] = pl
            if pl < cur_min_l and pitch_min_length_dm is None:
                struct.pack_into("<H", db, row_off + stad_layout.pitch_min_length_offset, pl)
            if pl > cur_max_l and pitch_max_length_dm is None:
                struct.pack_into("<H", db, row_off + stad_layout.pitch_max_length_offset, pl)
            cur_len = pl

        if pitch_width_dm is not None:
            pw = max(400, min(cur_len - 1, int(pitch_width_dm)))
            struct.pack_into("<H", db, row_off + stad_layout.pitch_width_offset, pw)
            modified["pitch_width_dm"] = pw
            if pw < cur_min_w and pitch_min_width_dm is None:
                struct.pack_into("<H", db, row_off + stad_layout.pitch_min_width_offset, pw)
            if pw > cur_max_w and pitch_max_width_dm is None:
                struct.pack_into("<H", db, row_off + stad_layout.pitch_max_width_offset, pw)

        if pitch_min_length_dm is not None:
            struct.pack_into(
                "<H", db, row_off + stad_layout.pitch_min_length_offset, int(pitch_min_length_dm)
            )
            modified["pitch_min_length_dm"] = int(pitch_min_length_dm)
        if pitch_max_length_dm is not None:
            struct.pack_into(
                "<H", db, row_off + stad_layout.pitch_max_length_offset, int(pitch_max_length_dm)
            )
            modified["pitch_max_length_dm"] = int(pitch_max_length_dm)
        if pitch_min_width_dm is not None:
            struct.pack_into(
                "<H", db, row_off + stad_layout.pitch_min_width_offset, int(pitch_min_width_dm)
            )
            modified["pitch_min_width_dm"] = int(pitch_min_width_dm)
        if pitch_max_width_dm is not None:
            struct.pack_into(
                "<H", db, row_off + stad_layout.pitch_max_width_offset, int(pitch_max_width_dm)
            )
            modified["pitch_max_width_dm"] = int(pitch_max_width_dm)

        if built_date is not None:
            write_packed_date_into(db, row_off + stad_layout.built_offset, built_date)
            modified["built_date"] = str(_coerce_date(built_date))
        if rebuilt_date is not None:
            write_packed_date_into(db, row_off + stad_layout.rebuilt_offset, rebuilt_date)
            modified["rebuilt_date"] = str(_coerce_date(rebuilt_date))
        if date_58 is not None:
            write_packed_date_into(db, row_off + stad_layout.date_58_offset, date_58)
            modified["date_58"] = str(_coerce_date(date_58))
        if u17 is not None:
            struct.pack_into("<I", db, row_off + stad_layout.u17_offset, int(u17))
            modified["u17"] = int(u17)
        if u25 is not None:
            struct.pack_into("<I", db, row_off + stad_layout.u25_offset, int(u25))
            modified["u25"] = int(u25)
        if b33 is not None:
            db[row_off + stad_layout.b33_offset] = int(b33) & 0xFF
            modified["b33"] = int(b33)
        if flags_156 is not None:
            struct.pack_into("<H", db, row_off + stad_layout.flags_offset, int(flags_156) & 0xFFFF)
            modified["flags_156"] = int(flags_156)

        if name is not None:
            flags_val = read_u16(db, row_off + stad_layout.flags_offset)
            if not (flags_val & stad_layout.inline_name_flag):
                raise ValueError(
                    f"Stadium {target_row.uid} does not carry an inline name flag; rename via name pool instead"
                )
            old_len = read_u32(db, row_off + stad_layout.name_length_offset)
            new_bytes = name.encode("utf-8")
            struct.pack_into("<I", db, row_off + stad_layout.name_length_offset, len(new_bytes))
            name_start = row_off + stad_layout.name_offset
            db[name_start : name_start + old_len] = new_bytes
            modified["name"] = name

        self._cached_stadium_index = None
        self._edit_log.append({"type": "edit_stadium", **modified})
        return modified

    def edit_affiliate_group(
        self,
        group_index: int,
        member_club_uids_or_names: Sequence[int | str],
    ) -> dict[str, Any]:
        """Update the member clubs of an affiliate group in `feeder_man.dat` (or append a new group
        when `group_index == -1` or `group_index == group_count`).
        """
        aff_buf = self.get_section_buffer(AFFILIATE_SECTION)
        aff_layout: AffiliateGroupLayout = self._layout(AffiliateGroupLayout, AFFILIATE_SECTION)

        member_indices: list[int] = []
        for item in member_club_uids_or_names:
            club_obj = self._resolve_club_record(item)
            member_indices.append(self._club_index_for_uid(club_obj.uid))

        if not (aff_layout.group_size_range[0] <= len(member_indices) <= aff_layout.group_size_range[1]):
            raise ValueError(f"Affiliate group size {len(member_indices)} outside valid range")

        group_count = read_u32(aff_buf, aff_layout.count_offset)
        cursor = aff_layout.groups_offset
        groups: list[tuple[int, ...]] = []
        for _ in range(group_count):
            m_cnt = read_u32(aff_buf, cursor)
            cursor += 4
            members = struct.unpack_from(f"<{m_cnt}I", aff_buf, cursor)
            groups.append(members)
            cursor += 4 * m_cnt

        tail = bytes(aff_buf[cursor:])
        if group_index == -1 or group_index == len(groups):
            groups.append(tuple(member_indices))
            target_idx = len(groups) - 1
        elif 0 <= group_index < len(groups):
            groups[group_index] = tuple(member_indices)
            target_idx = group_index
        else:
            raise IndexError(f"Affiliate group index {group_index} out of range (0..{len(groups)})")

        new_parts = [
            bytes(aff_buf[: aff_layout.count_offset]),
            struct.pack("<I", len(groups)),
        ]
        for grp in groups:
            new_parts.append(struct.pack(f"<{1 + len(grp)}I", len(grp), *grp))
        new_parts.append(tail)
        aff_buf[:] = b"".join(new_parts)

        rec = {
            "type": "edit_affiliate_group",
            "group_index": target_idx,
            "member_club_indices": member_indices,
        }
        self._edit_log.append(rec)
        return rec

    # ------------------------------------------------------------------
    # 6. Staff & Staff Lists (`staff`, `staff-lists`, `enrichment` in `game_db.dat`)
    # ------------------------------------------------------------------
    def _resolve_staff_record(self, staff_uid_or_name: int | str) -> tuple[int, int, int | None]:
        """Resolve a staff person by UID, person ID, or name to `(person_id, header_offset, contract_offset)`."""
        db = self._game_db_buf()
        staff_layout: StaffLayout = self._layout(StaffLayout)
        contract_layout: ContractLayout = self._layout(ContractLayout)
        humans_buf = self.get_section_buffer(HUMANS_SECTION)
        humans_layout: HumansLayout = self._layout(HumansLayout, HUMANS_SECTION)

        staff_table = self._save_reader.staff()
        target_staff = None
        if isinstance(staff_uid_or_name, int):
            for s in staff_table:
                if s.uid == staff_uid_or_name or (s.uid - 1) == staff_uid_or_name:
                    target_staff = s
                    break
        else:
            q = staff_uid_or_name.strip().lower()
            if q.isdigit():
                return self._resolve_staff_record(int(q))
            for s in staff_table:
                for cand in (s.name, s.full_name, s.common_name):
                    if cand and q in cand.lower():
                        target_staff = s
                        break
                if target_staff is not None:
                    break

        if target_staff is None:
            raise KeyError(f"Staff member matching {staff_uid_or_name!r} not found")

        from fm26save._core.readers.staff import _header_reader, _header_values

        reader = _header_reader(staff_layout)
        uid_bytes = struct.pack("<I", target_staff.uid)
        h_off: int | None = None
        pid: int | None = None
        pos = 0
        while True:
            u_hit = db.find(uid_bytes, pos)
            if u_hit < 0:
                break
            cand_h = u_hit - staff_layout.uid_offset
            vals = _header_values(db, cand_h, reader, staff_layout)
            if vals is not None and vals[1] in (staff_layout.staff_kind, staff_layout.human_kind):
                h_off = cand_h
                pid = read_u32(db, cand_h)
                break
            pos = u_hit + 1

        if h_off is None or pid is None:
            raise RuntimeError(f"Could not locate binary header for staff {target_staff.uid}")

        selector = pid + 1
        # Find contract tag offset for selector (pid + 1) after header
        c_off: int | None = None
        sel_bytes = struct.pack("<I", selector)
        search_end = (
            len(db)
            if target_staff.is_human_manager
            else min(len(db), h_off + staff_layout.contract_header_search_bytes + 512)
        )
        pos = h_off
        while True:
            hit = db.find(sel_bytes, pos, search_end)
            if hit < 0:
                break
            tag_at = hit - contract_layout.selector_offset
            if tag_at >= h_off and db[tag_at : tag_at + len(contract_layout.tag)] == contract_layout.tag:
                c_off = tag_at
                break
            pos = hit + 1

        return pid, h_off, c_off

    def edit_staff(
        self,
        staff_uid_or_name: int | str,
        *,
        current_ability: int | None = None,
        potential_ability: int | None = None,
        role_r4: int | None = None,
        codes: Sequence[int] | None = None,
        preferences: Mapping[str, int] | None = None,
        block_40_attributes: Sequence[int] | Mapping[int | str, int] | None = None,
        raw_block_40_scale: bool = False,
        birth_date: datetime.date | str | None = None,
        age: int | None = None,
        nation_id: int | None = None,
        personality: Mapping[str, int] | None = None,
        wage: int | None = None,
        contract_start: datetime.date | str | None = None,
        contract_end: datetime.date | str | None = None,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Modify any decoded or enriched field on a staff member in `game_db.dat`."""
        db = self._game_db_buf()
        staff_layout: StaffLayout = self._layout(StaffLayout)
        person_layout: PersonBlockLayout = self._layout(PersonBlockLayout)
        contract_layout: ContractLayout = self._layout(ContractLayout)

        pid, h_off, c_off = self._resolve_staff_record(staff_uid_or_name)
        uid = read_u32(db, h_off + staff_layout.uid_offset)
        entry_count = db[h_off + staff_layout.entry_count_offset]
        ability_off = (
            h_off
            + staff_layout.ability_base_offset
            + entry_count * staff_layout.entry_bytes
        )

        modified: dict[str, Any] = {
            "id": pid,
            "uid": uid,
            "header_offset": h_off,
            "ability_offset": ability_off,
        }

        if current_ability is not None:
            ca = max(1, min(200, int(current_ability)))
            struct.pack_into("<H", db, ability_off + staff_layout.current_ability_offset, ca)
            modified["current_ability"] = ca

        if potential_ability is not None:
            pa = max(-20, min(200, int(potential_ability)))
            struct.pack_into("<h", db, ability_off + staff_layout.potential_ability_offset, pa)
            modified["potential_ability"] = pa

        if role_r4 is not None:
            db[ability_off + staff_layout.r4_offset] = int(role_r4) & 0xFF
            modified["role_r4"] = int(role_r4)

        if codes is not None:
            if len(codes) > staff_layout.code_count:
                raise ValueError(f"Expected at most {staff_layout.code_count} staff role codes")
            for idx, c_val in enumerate(codes):
                if c_val not in staff_layout.code_set:
                    raise ValueError(
                        f"Staff code {c_val} not in valid code_set {sorted(staff_layout.code_set)}"
                    )
                db[ability_off + staff_layout.codes_offset + idx] = int(c_val)
            modified["codes"] = list(codes)

        if preferences:
            slot_by_name = dict(staff_layout.named_preference_slots)
            for slot_idx in staff_layout.unnamed_preference_slots:
                slot_by_name[f"p{slot_idx:02d}"] = slot_idx
            pref_base = ability_off + staff_layout.preferences_offset
            pref_changes: dict[str, int] = {}
            for pk, pv in preferences.items():
                pk_norm = pk.strip().lower()
                if pk_norm not in slot_by_name:
                    raise ValueError(f"Unknown staff preference {pk!r}. Valid: {list(slot_by_name)}")
                s_idx = slot_by_name[pk_norm]
                val = max(1, min(100 if s_idx == 13 else 20, int(pv)))
                db[pref_base + s_idx] = val
                pref_changes[pk_norm] = val
            modified["preferences"] = pref_changes

        if block_40_attributes is not None:
            b40_base = ability_off + staff_layout.block_40_offset
            b40_names = (
                "attacking", "defending", "fitness", "goalkeepers_distribution",
                "goalkeepers_handling", "goalkeepers_shot_stopping", "mental", "tactical",
                "technical", "working_with_youngsters", "judging_player_ability",
                "judging_player_potential", "judging_staff_ability", "negotiating",
                "physiotherapy", "sports_science", "man_management", "level_of_discipline",
                "motivating", "tactical_knowledge", "set_pieces", "data_analysis",
                "adaptability_role", "determination_role", "player_knowledge", "youth_knowledge",
            )
            if isinstance(block_40_attributes, Mapping):
                b40_changes: dict[str, int] = {}
                for k, v in block_40_attributes.items():
                    if isinstance(k, int) or str(k).isdigit():
                        idx = int(k)
                    else:
                        kn = str(k).strip().lower()
                        if kn.startswith("b") and kn[1:].isdigit():
                            idx = int(kn[1:]) - staff_layout.block_40_offset
                        elif kn in b40_names:
                            idx = b40_names.index(kn)
                        else:
                            raise ValueError(f"Unknown staff block_40 key {k!r}")
                    if not 0 <= idx < staff_layout.block_40_count:
                        raise IndexError(f"block_40 index {idx} out of range (0..25)")
                    raw_v = int(v) if (raw_block_40_scale or int(v) > 20) else int(v) * 5
                    raw_v = max(1, min(100, raw_v))
                    db[b40_base + idx] = raw_v
                    b40_changes[f"b{staff_layout.block_40_offset + idx}"] = raw_v
                modified["block_40"] = b40_changes
            else:
                seq_vals = [
                    max(1, min(100, int(v) if (raw_block_40_scale or int(v) > 20) else int(v) * 5))
                    for v in block_40_attributes
                ]
                for idx, rv in enumerate(seq_vals[: staff_layout.block_40_count]):
                    db[b40_base + idx] = rv
                modified["block_40"] = seq_vals[: staff_layout.block_40_count]

        # Staff PersonBlock
        if any(x is not None for x in (birth_date, age, nation_id, personality)):
            if c_off is not None:
                p_start = c_off + staff_layout.person_block_offset_after_tag
                p_end = min(len(db), p_start + staff_layout.person_block_search_bytes)
            else:
                p_start = h_off
                p_end = min(len(db), h_off + staff_layout.list_only_block_search_bytes)
            pblock = locate_person_block(
                db,
                p_start - person_layout.window_start_offset,
                p_end,
                person_layout,
            )
            if pblock is not None:
                b_off = pblock.birth_date_offset
                if age is not None and birth_date is None:
                    clock = self._save_reader.info.game_date or datetime.date(2025, 8, 1)
                    existing_bd = decode_date(db, b_off) or datetime.date(clock.year - int(age), 6, 15)
                    birth_date = datetime.date(clock.year - int(age), existing_bd.month, min(existing_bd.day, 28))
                if birth_date is not None:
                    write_packed_date_into(db, b_off, birth_date)
                    modified["birth_date"] = str(_coerce_date(birth_date))
                if nation_id is not None:
                    struct.pack_into(
                        "<H", db, b_off + person_layout.nation_id_offset_from_birth, int(nation_id)
                    )
                    modified["nation_id"] = int(nation_id)
                if personality:
                    pers_order = (
                        "adaptability", "ambition", "controversy", "loyalty",
                        "pressure", "professionalism", "sportsmanship", "temperament",
                    )
                    pers_base = b_off + person_layout.personality_offset_from_birth
                    for pk, pv in personality.items():
                        pk_norm = pk.strip().lower()
                        if pk_norm in pers_order:
                            db[pers_base + pers_order.index(pk_norm)] = max(1, min(20, int(pv)))
                    modified["personality"] = dict(personality)

        # Staff Contract
        if c_off is not None and any(
            x is not None for x in (wage, contract_start, contract_end, team_id)
        ):
            if wage is not None:
                struct.pack_into("<I", db, c_off + contract_layout.wage_offset, max(0, int(wage)))
                modified["wage"] = int(wage)
            if team_id is not None:
                struct.pack_into("<I", db, c_off + contract_layout.team_id_offset, int(team_id))
                modified["team_id"] = int(team_id)
            if contract_start is not None:
                write_packed_date_into(db, c_off + contract_layout.start_offset, contract_start)
                modified["contract_start"] = str(_coerce_date(contract_start))
            if contract_end is not None:
                clock = self.get_game_date() or datetime.date(2025, 7, 1)
                decoder = build_contract_decoder(
                    contract_layout, self._club_index(), clock, self.source_path.name
                )
                tail_e = decoder._locate_tail(db, c_off)
                if tail_e is not None:
                    write_packed_date_into(
                        db, tail_e + contract_layout.tail_end_offset, contract_end
                    )
                    modified["contract_end"] = str(_coerce_date(contract_end))

        self._edit_log.append({"type": "edit_staff", **modified})
        return modified

    def max_out_staff(
        self,
        staff_uid_or_name: int | str,
        *,
        ca: int = 200,
        pa: int = 200,
        attribute_value_20: int = 20,
    ) -> dict[str, Any]:
        """Maximize a staff member's CA/PA (200/200), all 26 coaching/scouting/medical attributes (20/20),
        and positive personality attributes.
        """
        raw_val = max(1, min(100, int(attribute_value_20) * 5))
        return self.edit_staff(
            staff_uid_or_name,
            current_ability=ca,
            potential_ability=pa,
            block_40_attributes=[raw_val] * 26,
            raw_block_40_scale=True,
            personality={
                "adaptability": 20,
                "ambition": 20,
                "controversy": 1,
                "loyalty": 20,
                "pressure": 20,
                "professionalism": 20,
                "sportsmanship": 20,
                "temperament": 20,
            },
        )

    def edit_club_staff_list(
        self,
        club_uid_or_name: int | str,
        slot: int,
        entry_index: int,
        new_staff_person_uid: int,
    ) -> dict[str, Any]:
        """Update an entry in one of a club's 3 staff lists (`slot` 0, 1, or 2) in `game_db.dat`."""
        db = self._game_db_buf()
        club = self._resolve_club_record(club_uid_or_name)
        span = self._club_span(club.uid)
        if span.team_list_end is None:
            raise KeyError(f"Club {club.name} ({club.uid}) has no team/staff list offset")

        staff_layout: StaffLayout = self._layout(StaffLayout)
        if not 0 <= slot < staff_layout.list_count:
            raise ValueError(f"Staff list slot {slot} must be in 0..{staff_layout.list_count - 1}")

        # Advance past affiliate list (count byte + u32 entries)
        cursor = span.team_list_end + 1 + 4 * db[span.team_list_end]

        for s_idx in range(staff_layout.list_count):
            cnt = db[cursor]
            cursor += 1
            if s_idx == slot:
                if not 0 <= entry_index < cnt:
                    raise IndexError(f"Entry index {entry_index} out of range (0..{cnt - 1})")
                target_off = cursor + 4 * entry_index
                old_sel = read_u32(db, target_off)
                # Stored value is selector = person_id + 1
                if int(new_staff_person_uid) == 0:
                    new_sel = 0
                else:
                    try:
                        s_pid, _sh, _sc = self._resolve_staff_record(int(new_staff_person_uid))
                        new_sel = s_pid + 1
                    except KeyError:
                        new_sel = int(new_staff_person_uid)
                struct.pack_into("<I", db, target_off, new_sel)
                rec = {
                    "type": "edit_club_staff_list",
                    "club_uid": club.uid,
                    "slot": slot,
                    "entry_index": entry_index,
                    "old_staff_uid": old_sel,
                    "new_staff_uid": new_sel,
                }
                self._edit_log.append(rec)
                return rec
            cursor += 4 * cnt
        raise RuntimeError("Failed to locate staff list slot")

    # ------------------------------------------------------------------
    # 7. Tactics, Set Pieces, Training, Mentoring, Job Vacancies
    # ------------------------------------------------------------------
    def edit_tactics_lineup(
        self,
        slot_index: int,
        player_uid_or_name: int | str | None,
        *,
        team_block_index: int = 0,
    ) -> dict[str, Any]:
        """Set or clear a player in one of the 26 lineup/bench selector slots (`0..25`) in `tactics_man.dat`."""
        tac_buf = self.get_section_buffer(TACTICS_SECTION)
        tac_layout: TacticsLayout = self._layout(TacticsLayout, TACTICS_SECTION)

        if not 0 <= slot_index < tac_layout.selection_slot_count:
            raise IndexError(
                f"Lineup slot_index {slot_index} out of range (0..{tac_layout.selection_slot_count - 1})"
            )

        if player_uid_or_name is None or player_uid_or_name == 0:
            new_selector = 0
            resolved_uid = None
        else:
            prec = self._player_records()
            pos_idx, _rec_off, resolved_uid = self._resolve_player_position(player_uid_or_name)
            new_selector = prec.pindexes[pos_idx] + 1

        # Locate each team block's selection slot array via _stored_block_starts
        from fm26save._core.readers.tactics import _stored_block_starts

        block_starts = _stored_block_starts(tac_buf, tac_layout, self.source_path.name)
        found_blocks: list[int] = []
        for b_start in block_starts:
            after_marker = b_start + 4 + len(tac_layout.block_marker)
            _lbl, sel_start = read_length_prefixed_string(
                tac_buf, after_marker, tac_layout.name_length_range[1]
            )
            found_blocks.append(sel_start)

        if not 0 <= team_block_index < len(found_blocks):
            raise IndexError(
                f"team_block_index {team_block_index} out of range (found {len(found_blocks)} blocks)"
            )

        target_off = found_blocks[team_block_index] + 4 * slot_index
        old_selector = read_u32(tac_buf, target_off)
        struct.pack_into("<I", tac_buf, target_off, new_selector)

        rec = {
            "type": "edit_tactics_lineup",
            "team_block_index": team_block_index,
            "slot_index": slot_index,
            "old_selector": old_selector,
            "new_selector": new_selector,
            "player_uid": resolved_uid,
        }
        self._edit_log.append(rec)
        return rec

    def edit_tactic_record(
        self,
        tactic_index: int = 0,
        *,
        mentality: int | None = None,
        style_code: str | None = None,
        team_instructions: Mapping[int, int] | Sequence[int] | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Modify a tactic record's `mentality` (`1..5`), `style_code` (4 ASCII chars),
        `team_instructions` (18 bytes), or `name` in `tactics_man.dat`.
        """
        tac_buf = self.get_section_buffer(TACTICS_SECTION)
        tac_layout: TacticsLayout = self._layout(TacticsLayout, TACTICS_SECTION)

        sigs = (
            tac_layout.user_signature,
            tac_layout.alternate_signature,
            tac_layout.preset_signature,
        )
        hits: list[tuple[int, bytes]] = []
        for s in sigs:
            p = 0
            while (h := tac_buf.find(s, p)) != -1:
                hits.append((h, s))
                p = h + 1
        hits.sort(key=lambda x: x[0])
        if not 0 <= tactic_index < len(hits):
            raise IndexError(f"tactic_index {tactic_index} out of range (found {len(hits)} tactic records)")

        sig_off, sig_bytes = hits[tactic_index]
        name_len_off = sig_off + len(sig_bytes)
        cur_name, name_end = read_length_prefixed_string(
            tac_buf, name_len_off, tac_layout.name_length_range[1]
        )
        instr_start = name_end + tac_layout.name_zero_bytes
        _style_lbl, style_start = read_length_prefixed_string(
            tac_buf,
            instr_start + tac_layout.team_instruction_bytes,
            tac_layout.name_length_range[1],
        )

        modified: dict[str, Any] = {"tactic_index": tactic_index, "offset": sig_off}

        if mentality is not None:
            m_val = max(1, min(5, int(mentality)))
            tac_buf[instr_start + tac_layout.mentality_index] = m_val
            modified["mentality"] = m_val

        if team_instructions is not None:
            non_mentality_indices = [
                i for i in range(tac_layout.team_instruction_bytes) if i != tac_layout.mentality_index
            ]
            if isinstance(team_instructions, Mapping):
                for k, v in team_instructions.items():
                    idx = non_mentality_indices[int(k)]
                    tac_buf[instr_start + idx] = int(v) & 0xFF
            else:
                for k, v in enumerate(team_instructions[: len(non_mentality_indices)]):
                    tac_buf[instr_start + non_mentality_indices[k]] = int(v) & 0xFF
            modified["team_instructions_updated"] = True

        if style_code is not None:
            sc_bytes = style_code.encode("ascii")
            if len(sc_bytes) != tac_layout.style_code_bytes:
                raise ValueError(f"style_code must be exactly {tac_layout.style_code_bytes} ASCII chars")
            tac_buf[style_start : style_start + tac_layout.style_code_bytes] = sc_bytes
            modified["style_code"] = style_code

        if name is not None:
            nb = name.encode("utf-8")
            tac_buf[name_len_off:name_end] = struct.pack("<I", len(nb)) + nb
            modified["name"] = name

        self._edit_log.append({"type": "edit_tactic_record", **modified})
        return modified

    def edit_training_week(
        self,
        team_block_index: int,
        week_index: int,
        *,
        schedule_name: str | None = None,
        week_start_date: datetime.date | str | None = None,
    ) -> dict[str, Any]:
        """Edit a weekly training schedule record in `training_man.dat`."""
        tr_buf = self.get_section_buffer(TRAINING_SECTION)
        tr_layout: TrainingLayout = self._layout(TrainingLayout, TRAINING_SECTION)

        hdr_entries = read_u32(tr_buf, tr_layout.header_count_offset)
        cursor = (
            tr_layout.header_list_offset
            + tr_layout.header_entry_bytes * hdr_entries
            + tr_layout.header_gap_bytes
        )
        for b_idx in range(team_block_index + 1):
            lead_off = cursor + 4
            entry_cnt = read_u32(tr_buf, lead_off + 1)
            weeks_cnt_off = lead_off + 5 + entry_cnt * tr_layout.block_entry_bytes
            wk_cnt = read_u32(tr_buf, weeks_cnt_off)
            pos = weeks_cnt_off + 4
            for w_idx in range(wk_cnt):
                _, name_end = read_length_prefixed_string(
                    tr_buf, pos + tr_layout.week_name_offset, tr_layout.longest_name_bytes
                )
                rec_end = name_end + tr_layout.week_trailer_bytes
                if b_idx == team_block_index and w_idx == week_index:
                    modified: dict[str, Any] = {
                        "team_block_index": team_block_index,
                        "week_index": week_index,
                    }
                    if week_start_date is not None:
                        write_packed_date_into(
                            tr_buf, pos + tr_layout.week_date_offset, week_start_date
                        )
                        modified["week_start_date"] = str(_coerce_date(week_start_date))
                    if schedule_name is not None:
                        nb = schedule_name.encode("utf-8")
                        name_len_off = pos + tr_layout.week_name_offset
                        struct.pack_into("<I", tr_buf, name_len_off, len(nb))
                        tr_buf[name_len_off + 4 : name_end] = nb
                        modified["schedule_name"] = schedule_name
                    self._edit_log.append({"type": "edit_training_week", **modified})
                    return modified
                pos = rec_end
            grp_cnt_off = pos + tr_layout.block_tail_bytes
            grp_cnt = read_u32(tr_buf, grp_cnt_off)
            pos = grp_cnt_off + 4
            for _ in range(grp_cnt):
                lbl_off = pos + 6
                _, after_lbl = read_length_prefixed_string(
                    tr_buf, lbl_off, tr_layout.longest_name_bytes
                )
                m_cnt = read_u32(tr_buf, after_lbl)
                pos = after_lbl + 4 + 4 * m_cnt
            cursor = pos + 1
        raise IndexError(f"Training week ({team_block_index}, {week_index}) not found")

    def edit_mentoring_group(
        self,
        team_block_index: int,
        group_index: int,
        *,
        label: str | None = None,
        member_player_uids_or_names: Sequence[int | str] | None = None,
    ) -> dict[str, Any]:
        """Modify a mentoring group's label or member players in `training_man.dat`."""
        tr_buf = self.get_section_buffer(TRAINING_SECTION)
        tr_layout: TrainingLayout = self._layout(TrainingLayout, TRAINING_SECTION)
        prec = self._player_records()

        hdr_entries = read_u32(tr_buf, tr_layout.header_count_offset)
        cursor = (
            tr_layout.header_list_offset
            + tr_layout.header_entry_bytes * hdr_entries
            + tr_layout.header_gap_bytes
        )
        for b_idx in range(team_block_index + 1):
            lead_off = cursor + 4
            entry_cnt = read_u32(tr_buf, lead_off + 1)
            weeks_cnt_off = lead_off + 5 + entry_cnt * tr_layout.block_entry_bytes
            wk_cnt = read_u32(tr_buf, weeks_cnt_off)
            pos = weeks_cnt_off + 4
            for _ in range(wk_cnt):
                _, name_end = read_length_prefixed_string(
                    tr_buf, pos + tr_layout.week_name_offset, tr_layout.longest_name_bytes
                )
                pos = name_end + tr_layout.week_trailer_bytes
            grp_cnt_off = pos + tr_layout.block_tail_bytes
            grp_cnt = read_u32(tr_buf, grp_cnt_off)
            pos = grp_cnt_off + 4
            for g_idx in range(grp_cnt):
                lbl_off = pos + 6
                cur_lbl, after_lbl = read_length_prefixed_string(
                    tr_buf, lbl_off, tr_layout.longest_name_bytes
                )
                m_cnt = read_u32(tr_buf, after_lbl)
                grp_end = after_lbl + 4 + 4 * m_cnt
                if b_idx == team_block_index and g_idx == group_index:
                    new_lbl = label if label is not None else cur_lbl
                    if member_player_uids_or_names is not None:
                        new_selectors = []
                        for p_item in member_player_uids_or_names:
                            p_pos, _ro, _uid = self._resolve_player_position(p_item)
                            new_selectors.append(prec.pindexes[p_pos] + 1)
                    else:
                        new_selectors = list(struct.unpack_from(f"<{m_cnt}I", tr_buf, after_lbl + 4))
                    lbl_bytes = new_lbl.encode("utf-8")
                    replacement = (
                        struct.pack("<I", len(lbl_bytes))
                        + lbl_bytes
                        + struct.pack(f"<{1 + len(new_selectors)}I", len(new_selectors), *new_selectors)
                    )
                    tr_buf[lbl_off:grp_end] = replacement
                    rec = {
                        "type": "edit_mentoring_group",
                        "team_block_index": team_block_index,
                        "group_index": group_index,
                        "label": new_lbl,
                        "member_selectors": new_selectors,
                    }
                    self._edit_log.append(rec)
                    return rec
                pos = grp_end
            if b_idx == team_block_index and group_index == grp_cnt:
                new_lbl = label if label is not None else f"Mentoring Group {group_index + 1}"
                new_selectors = []
                if member_player_uids_or_names is not None:
                    for p_item in member_player_uids_or_names:
                        p_pos, _ro, _uid = self._resolve_player_position(p_item)
                        new_selectors.append(prec.pindexes[p_pos] + 1)
                lbl_bytes = new_lbl.encode("utf-8")
                new_group_bytes = (
                    struct.pack(
                        "<BIBI",
                        tr_layout.group_lead_byte,
                        group_index + 1,
                        tr_layout.group_label_marker,
                        len(lbl_bytes),
                    )
                    + lbl_bytes
                    + struct.pack(f"<{1 + len(new_selectors)}I", len(new_selectors), *new_selectors)
                )
                struct.pack_into("<I", tr_buf, grp_cnt_off, grp_cnt + 1)
                tr_buf[pos:pos] = new_group_bytes
                rec = {
                    "type": "edit_mentoring_group",
                    "team_block_index": team_block_index,
                    "group_index": group_index,
                    "created": True,
                    "label": new_lbl,
                    "member_selectors": new_selectors,
                }
                self._edit_log.append(rec)
                return rec
            cursor = pos + 1
        raise IndexError(f"Mentoring group ({team_block_index}, {group_index}) not found")

    def edit_job_vacancy(
        self,
        vacancy_index: int,
        *,
        team_id: int | None = None,
        advertised_date: datetime.date | str | None = None,
        competition_id: int | None = None,
        league_position: int | None = None,
        role: int | None = None,
        flag: int | None = None,
    ) -> dict[str, Any]:
        """Modify an open job vacancy record in `job_centre.dat`."""
        job_buf = self.get_section_buffer(JOB_CENTRE_SECTION)
        job_layout: JobCentreLayout = self._layout(JobCentreLayout, JOB_CENTRE_SECTION)

        stored_count = read_u32(job_buf, job_layout.count_offset)
        idx = stored_count + vacancy_index if vacancy_index < 0 else vacancy_index
        if not 0 <= idx < stored_count:
            raise IndexError(f"Job vacancy index {vacancy_index} out of range (0..{stored_count - 1})")

        cursor = job_layout.records_offset
        for _ in range(idx):
            id_cnt = job_buf[cursor + job_layout.id_count_offset]
            cursor += job_layout.record_bytes + job_layout.id_bytes * id_cnt

        id_cnt = job_buf[cursor + job_layout.id_count_offset]
        tail_shift = job_layout.id_bytes * id_cnt
        modified: dict[str, Any] = {"vacancy_index": idx, "offset": cursor}

        if team_id is not None:
            t_val = 0 if team_id <= 0 else int(team_id)
            struct.pack_into("<I", job_buf, cursor + job_layout.team_id_offset, t_val)
            modified["team_id"] = t_val
        if role is not None:
            job_buf[cursor + job_layout.role_offset] = int(role) & 0xFF
            modified["role"] = int(role)
        if advertised_date is not None:
            write_packed_date_into(job_buf, cursor + job_layout.advertised_offset, advertised_date)
            # Ensure second_date at date_12_offset is >= advertised_date so dates_ordered holds
            adv_d = _coerce_date(advertised_date)
            sec_d = decode_date(job_buf, cursor + job_layout.date_12_offset)
            if adv_d is not None and (sec_d is None or sec_d < adv_d):
                write_packed_date_into(job_buf, cursor + job_layout.date_12_offset, adv_d)
            modified["advertised_date"] = str(adv_d)
        if competition_id is not None:
            c_val = job_layout.no_competition if competition_id < 0 else int(competition_id) & 0xFFFF
            struct.pack_into(
                "<H", job_buf, cursor + tail_shift + job_layout.competition_offset, c_val
            )
            modified["competition_id"] = None if c_val == job_layout.no_competition else c_val
        if league_position is not None:
            job_buf[cursor + tail_shift + job_layout.league_position_offset] = (
                int(league_position) & 0xFF
            )
            modified["league_position"] = int(league_position)
        if flag is not None:
            job_buf[cursor + tail_shift + job_layout.flag_offset] = int(flag) & 0xFF
            modified["flag"] = int(flag)

        self._edit_log.append({"type": "edit_job_vacancy", **modified})
        return modified

    def edit_set_piece_routine(
        self,
        routine_index_or_name: int | str,
        *,
        name: str | None = None,
        flag_a: int | None = None,
        flag_b: int | None = None,
    ) -> dict[str, Any]:
        """Modify a set-piece routine's name or flags in `tactics_man.dat`."""
        from fm26save._core.readers.tactics import (
            _read_routine_groups,
            _read_routine_name,
            _routine_tail_pattern,
        )

        tac_buf = self.get_section_buffer(TACTICS_SECTION)
        tac_layout: TacticsLayout = self._layout(TacticsLayout, TACTICS_SECTION)
        routines: list[tuple[int, int, str]] = []
        area = tac_buf.find(tac_layout.routine_area_marker)
        while area >= 0:
            _rnames, complete = _read_routine_groups(tac_buf, area, len(tac_buf), tac_layout)
            if complete:
                break
            area = tac_buf.find(tac_layout.routine_area_marker, area + 1)
        search_start = area + tac_layout.routine_area_header_bytes if area >= 0 else 0
        for m in _routine_tail_pattern(tac_layout).finditer(bytes(tac_buf), search_start):
            terminator = m.start()
            r_name = _read_routine_name(tac_buf, terminator, tac_layout)
            if r_name is not None and m.end() + 1 <= len(tac_buf):
                name_start = terminator - 4 - len(r_name.encode("utf-8"))
                if name_start >= search_start:
                    routines.append((name_start, terminator, r_name))

        target_idx: int | None = None
        if isinstance(routine_index_or_name, int):
            idx = len(routines) + routine_index_or_name if routine_index_or_name < 0 else routine_index_or_name
            if 0 <= idx < len(routines):
                target_idx = idx
        else:
            q = routine_index_or_name.strip().lower()
            for i, (_ns, _ne, rn) in enumerate(routines):
                if rn.lower() == q or q in rn.lower():
                    target_idx = i
                    break
        if target_idx is None:
            raise KeyError(f"Set-piece routine {routine_index_or_name!r} not found")

        name_start, name_end, cur_name = routines[target_idx]
        modified: dict[str, Any] = {"routine_index": target_idx, "old_name": cur_name}
        if flag_a is not None:
            f_lo, f_hi = tac_layout.routine_tail_flag_range
            fa_val = max(f_lo, min(f_hi, int(flag_a)))
            tac_buf[name_end] = fa_val
            modified["flag_a"] = fa_val
        if flag_b is not None:
            tac_buf[name_end + 1 + tac_layout.routine_code_bytes] = int(flag_b) & 0xFF
            modified["flag_b"] = int(flag_b)
        if name is not None:
            nb = name.encode("utf-8")
            tac_buf[name_start:name_end] = struct.pack("<I", len(nb)) + nb
            modified["name"] = name
        self._edit_log.append({"type": "edit_set_piece_routine", **modified})
        return modified

    # ------------------------------------------------------------------
    # 8. Competitions, Stages, League Tables, Fixtures, Rules, Transfers & Player Stats
    # ------------------------------------------------------------------
    def edit_stage(
        self,
        stage_id_or_index: int,
        *,
        competition_id: int | None = None,
        group_id: int | None = None,
        round_number: int | None = None,
        previous_stage_id: int | None = None,
        s25: int | None = None,
        s29: int | None = None,
    ) -> dict[str, Any]:
        """Modify a stage row in `game_db.dat`'s stage table."""
        db = self._game_db_buf()
        stage_layout: StageTableLayout = self._layout(StageTableLayout)
        scan = _stage_table_scan(stage_layout)
        table_start = find_table_start(db, scan)
        if table_start is None:
            raise RuntimeError("Could not locate stage table in game_db.dat")

        # Walk rows just like stages._walk_rows
        buf_len = len(db)
        row_offsets: list[tuple[int, int]] = []
        cursor = table_start
        while cursor + stage_layout.row_bytes <= buf_len:
            if _row_decodes(db, cursor, scan, buf_len):
                sid = read_u32(db, cursor + stage_layout.stage_id_offset)
                row_offsets.append((sid, cursor))
                cursor += stage_layout.row_bytes
            else:
                resync = -1
                cand = cursor + 1
                furthest = min(cursor + scan.resynchronisation_bytes, buf_len - stage_layout.row_bytes)
                while cand <= furthest:
                    if db[cand + scan.zero_byte_offset] == 0 and _row_decodes(db, cand, scan, buf_len):
                        resync = cand
                        break
                    cand += 1
                if resync < 0:
                    break
                cursor = resync

        target_off: int | None = None
        target_sid: int | None = None
        for sid, off in row_offsets:
            if sid == stage_id_or_index:
                target_sid, target_off = sid, off
                break
        if target_off is None and 0 <= stage_id_or_index < len(row_offsets):
            target_sid, target_off = row_offsets[stage_id_or_index]
        if target_off is None:
            raise KeyError(f"Stage {stage_id_or_index} not found in stage table")

        modified: dict[str, Any] = {"stage_id": target_sid, "offset": target_off}
        if competition_id is not None:
            c_val = stage_layout.competition_id_limit if competition_id < 0 else int(competition_id)
            struct.pack_into("<I", db, target_off + stage_layout.competition_id_offset, c_val)
            modified["competition_id"] = None if competition_id < 0 else int(competition_id)
        if group_id is not None:
            struct.pack_into("<I", db, target_off + stage_layout.group_id_offset, int(group_id))
            modified["group_id"] = int(group_id)
        if round_number is not None:
            struct.pack_into("<I", db, target_off + stage_layout.round_offset, int(round_number))
            modified["round"] = int(round_number)
        if previous_stage_id is not None:
            p_val = MISSING_REFERENCE if previous_stage_id < 0 else int(previous_stage_id)
            struct.pack_into("<I", db, target_off + stage_layout.previous_stage_id_offset, p_val)
            modified["previous_stage_id"] = None if previous_stage_id < 0 else int(previous_stage_id)
        if s25 is not None:
            struct.pack_into("<I", db, target_off + stage_layout.unknown_s25_offset, int(s25))
            modified["s25"] = int(s25)
        if s29 is not None:
            struct.pack_into("<I", db, target_off + stage_layout.unknown_s29_offset, int(s29))
            modified["s29"] = int(s29)

        self._edit_log.append({"type": "edit_stage", **modified})
        return modified

    def edit_competition_database_id(
        self,
        competition_id: int,
        *,
        database_id: int,
    ) -> dict[str, Any]:
        """Update a competition's editor `database_id` (both primary and copy fields) in `game_db.dat`."""
        db = self._game_db_buf()
        pair_layout: CompetitionIdPairLayout = self._layout(CompetitionIdPairLayout)
        marker = pair_layout.marker
        ent_lo, ent_hi = pair_layout.entity_id_range
        db_lo, db_hi = pair_layout.database_id_range
        if not db_lo <= database_id <= db_hi:
            raise ValueError(f"database_id {database_id} outside valid range {pair_layout.database_id_range}")

        pos = 0
        updated_offsets: list[int] = []
        while True:
            hit = db.find(marker, pos)
            if hit < 0:
                break
            rec_start = hit + pair_layout.record_offset_from_marker
            if 0 <= rec_start and rec_start + 32 <= len(db):
                ent_id = read_u32(db, rec_start + pair_layout.entity_id_offset)
                cur_db_id = read_u32(db, rec_start + pair_layout.database_id_offset)
                cur_copy = read_u32(db, rec_start + pair_layout.database_id_copy_offset)
                if (
                    ent_id == competition_id
                    and ent_lo <= ent_id <= ent_hi
                    and cur_db_id == cur_copy
                    and all(db[rec_start + off] == val for off, val in pair_layout.constant_bytes)
                ):
                    struct.pack_into(
                        "<I", db, rec_start + pair_layout.database_id_offset, int(database_id)
                    )
                    struct.pack_into(
                        "<I", db, rec_start + pair_layout.database_id_copy_offset, int(database_id)
                    )
                    updated_offsets.append(rec_start)
            pos = hit + 1

        if not updated_offsets:
            raise KeyError(f"Competition ID pair for competition_id={competition_id} not found")
        rec = {
            "type": "edit_competition_database_id",
            "competition_id": competition_id,
            "database_id": int(database_id),
            "updated_offsets": updated_offsets,
        }
        self._edit_log.append(rec)
        return rec

    def edit_league_table_row(
        self,
        team_id: int,
        *,
        won: int | None = None,
        drawn: int | None = None,
        lost: int | None = None,
        goals_for: int | None = None,
        goals_against: int | None = None,
        points: int | None = None,
        home_won: int | None = None,
        home_drawn: int | None = None,
        home_lost: int | None = None,
        home_goals_for: int | None = None,
        home_goals_against: int | None = None,
        home_points: int | None = None,
        away_won: int | None = None,
        away_drawn: int | None = None,
        away_lost: int | None = None,
        away_goals_for: int | None = None,
        away_goals_against: int | None = None,
        away_points: int | None = None,
        flag: int | None = None,
    ) -> dict[str, Any]:
        """Modify a team's league table standings across all matching `RawTableBlock` copies in `SPAN_REGION`.

        Automatically preserves all `_core` invariants:
        - `played == played_copy == won + drawn + lost` on all 5 aggregate rows
        - `total == home + away` for `played`, `won`, `drawn`, `lost`, `goals_for`, and `goals_against`
        - `first_half.played + second_half.played == total.played`
        - `total.played >= 1`
        """
        tbl_layout: LeagueTableLayout = find_layout(
            LeagueTableLayout, SPAN_REGION, None, self.version.build
        ).layout
        span_records = self._scan_span_records()
        matching_blocks = [b for b in span_records.table_blocks if b.team_id == team_id]
        if not matching_blocks:
            raise KeyError(f"No league table blocks found in SPAN_REGION for team_id={team_id}")

        row_sz = tbl_layout.row_bytes
        updated_span_offsets: list[int] = []
        final_summary: dict[str, Any] = {}

        for block in matching_blocks:
            base = block.span_offset
            raw_agg = bytearray(self.read_span_bytes(base, row_sz * tbl_layout.aggregate_count))

            def _read_r(idx: int) -> dict[str, int]:
                r_off = idx * row_sz
                return {
                    "played": raw_agg[r_off + tbl_layout.played_offset],
                    "won": raw_agg[r_off + tbl_layout.won_offset],
                    "drawn": raw_agg[r_off + tbl_layout.drawn_offset],
                    "lost": raw_agg[r_off + tbl_layout.lost_offset],
                    "gf": read_u16(raw_agg, r_off + tbl_layout.goals_for_offset),
                    "ga": read_u16(raw_agg, r_off + tbl_layout.goals_against_offset),
                    "pts": read_u16(raw_agg, r_off + tbl_layout.points_offset),
                    "flag": struct.unpack_from("<b", raw_agg, r_off + tbl_layout.flag_offset)[0],
                }

            def _write_r(idx: int, r: dict[str, int]) -> None:
                r_off = idx * row_sz
                p = r["won"] + r["drawn"] + r["lost"]
                raw_agg[r_off + tbl_layout.played_offset] = p & 0xFF
                raw_agg[r_off + tbl_layout.played_copy_offset] = p & 0xFF
                raw_agg[r_off + tbl_layout.won_offset] = r["won"] & 0xFF
                raw_agg[r_off + tbl_layout.drawn_offset] = r["drawn"] & 0xFF
                raw_agg[r_off + tbl_layout.lost_offset] = r["lost"] & 0xFF
                struct.pack_into("<H", raw_agg, r_off + tbl_layout.goals_for_offset, r["gf"] & 0xFFFF)
                struct.pack_into("<H", raw_agg, r_off + tbl_layout.goals_against_offset, r["ga"] & 0xFFFF)
                struct.pack_into("<H", raw_agg, r_off + tbl_layout.points_offset, r["pts"] & 0xFFFF)
                struct.pack_into("<b", raw_agg, r_off + tbl_layout.flag_offset, int(r["flag"]))

            r_tot = _read_r(0)
            r_home = _read_r(1)
            r_away = _read_r(2)
            r_fh = _read_r(3)
            r_sh = _read_r(4)

            # Apply explicit home/away overrides first
            if away_won is not None:
                r_away["won"] = int(away_won)
            if away_drawn is not None:
                r_away["drawn"] = int(away_drawn)
            if away_lost is not None:
                r_away["lost"] = int(away_lost)
            if away_goals_for is not None:
                r_away["gf"] = int(away_goals_for)
            if away_goals_against is not None:
                r_away["ga"] = int(away_goals_against)

            if home_won is not None:
                r_home["won"] = int(home_won)
            elif won is not None:
                r_home["won"] = max(0, int(won) - r_away["won"])
                r_away["won"] = int(won) - r_home["won"]

            if home_drawn is not None:
                r_home["drawn"] = int(home_drawn)
            elif drawn is not None:
                r_home["drawn"] = max(0, int(drawn) - r_away["drawn"])
                r_away["drawn"] = int(drawn) - r_home["drawn"]

            if home_lost is not None:
                r_home["lost"] = int(home_lost)
            elif lost is not None:
                r_home["lost"] = max(0, int(lost) - r_away["lost"])
                r_away["lost"] = int(lost) - r_home["lost"]

            if home_goals_for is not None:
                r_home["gf"] = int(home_goals_for)
            elif goals_for is not None:
                r_home["gf"] = max(0, int(goals_for) - r_away["gf"])
                r_away["gf"] = int(goals_for) - r_home["gf"]

            if home_goals_against is not None:
                r_home["ga"] = int(home_goals_against)
            elif goals_against is not None:
                r_home["ga"] = max(0, int(goals_against) - r_away["ga"])
                r_away["ga"] = int(goals_against) - r_home["ga"]

            r_home["pts"] = (
                int(home_points)
                if home_points is not None
                else 3 * r_home["won"] + r_home["drawn"]
            )
            r_away["pts"] = (
                int(away_points)
                if away_points is not None
                else 3 * r_away["won"] + r_away["drawn"]
            )

            # Recompute total row from home + away
            r_tot["won"] = r_home["won"] + r_away["won"]
            r_tot["drawn"] = r_home["drawn"] + r_away["drawn"]
            r_tot["lost"] = r_home["lost"] + r_away["lost"]
            r_tot["gf"] = r_home["gf"] + r_away["gf"]
            r_tot["ga"] = r_home["ga"] + r_away["ga"]
            r_tot["pts"] = int(points) if points is not None else (r_home["pts"] + r_away["pts"])
            if flag is not None:
                r_tot["flag"] = int(flag)

            new_total_played = r_tot["won"] + r_tot["drawn"] + r_tot["lost"]
            if new_total_played <= 0:
                raise ValueError("League table row total played must be >= 1")

            # Keep first_half.played + second_half.played == new_total_played
            fh_played = r_fh["won"] + r_fh["drawn"] + r_fh["lost"]
            sh_played = r_sh["won"] + r_sh["drawn"] + r_sh["lost"]
            if fh_played + sh_played != new_total_played:
                target_fh = max(0, new_total_played - sh_played)
                if target_fh + sh_played != new_total_played:
                    r_sh["won"] = 0
                    r_sh["drawn"] = 0
                    r_sh["lost"] = 0
                    target_fh = new_total_played
                # Adjust r_fh drawn/won/lost to sum to target_fh
                if r_fh["won"] + r_fh["lost"] <= target_fh:
                    r_fh["drawn"] = target_fh - (r_fh["won"] + r_fh["lost"])
                else:
                    r_fh["won"] = target_fh
                    r_fh["drawn"] = 0
                    r_fh["lost"] = 0

            _write_r(0, r_tot)
            _write_r(1, r_home)
            _write_r(2, r_away)
            _write_r(3, r_fh)
            _write_r(4, r_sh)

            self.patch_span_bytes(base, raw_agg)
            updated_span_offsets.append(base)
            final_summary = {
                "team_id": team_id,
                "played": new_total_played,
                "won": r_tot["won"],
                "drawn": r_tot["drawn"],
                "lost": r_tot["lost"],
                "goals_for": r_tot["gf"],
                "goals_against": r_tot["ga"],
                "points": r_tot["pts"],
                "updated_blocks": len(updated_span_offsets),
            }

        self._edit_log.append({"type": "edit_league_table_row", **final_summary})
        return final_summary

    def edit_fixture(
        self,
        *,
        fixture_span_offset: int | None = None,
        home_team_id: int | None = None,
        away_team_id: int | None = None,
        match_date: datetime.date | str | None = None,
        new_date: datetime.date | str | None = None,
        new_kick_off_time: datetime.time | str | None = None,
        new_home_team_id: int | None = None,
        new_away_team_id: int | None = None,
        new_home_goals: int | None = None,
        new_away_goals: int | None = None,
        new_played: bool | None = None,
        new_round_index: int | None = None,
    ) -> dict[str, Any]:
        """Modify a fixture in `SPAN_REGION` and synchronize its score across `SPAN_REGION`,
        result sections, and `game_db.dat` match summaries.
        """
        fix_layout: FixtureCalendarLayout = find_layout(
            FixtureCalendarLayout, SPAN_REGION, None, self.version.build
        ).layout
        res_layout: StageResultLayout = find_layout(
            StageResultLayout, SPAN_REGION, None, self.version.build
        ).layout
        span_records = self._scan_span_records()
        target_date = _coerce_date(match_date)

        all_raw_fixtures = list(span_records.fixtures)
        for cont in span_records.fixture_continuations:
            all_raw_fixtures.extend(cont.fixtures)

        matched_fixtures = []
        for rf in all_raw_fixtures:
            if fixture_span_offset is not None and rf.span_offset == fixture_span_offset:
                matched_fixtures.append(rf)
                break
            if home_team_id is not None and rf.home_team_id != home_team_id:
                continue
            if away_team_id is not None and rf.away_team_id != away_team_id:
                continue
            if target_date is not None:
                rf_bytes = struct.pack("<HH", rf.packed_kick_off, rf.kick_off_year)
                if decode_date(rf_bytes, 0) != target_date:
                    continue
            if home_team_id is not None or away_team_id is not None or target_date is not None:
                matched_fixtures.append(rf)

        if not matched_fixtures:
            raise KeyError("No matching fixture found in SPAN_REGION")

        # Identify the canonical (home_team_id, away_team_id, date, stage_id) of the first match
        primary = matched_fixtures[0]
        prim_date = decode_date(struct.pack("<HH", primary.packed_kick_off, primary.kick_off_year), 0)
        target_all = [
            rf
            for rf in all_raw_fixtures
            if rf.home_team_id == primary.home_team_id
            and rf.away_team_id == primary.away_team_id
            and decode_date(struct.pack("<HH", rf.packed_kick_off, rf.kick_off_year), 0) == prim_date
        ]

        updated_fixture_offsets: list[int] = []
        for rf in target_all:
            base = rf.span_offset
            rec_buf = bytearray(self.read_span_bytes(base, fix_layout.record_bytes))
            if new_home_team_id is not None:
                struct.pack_into("<I", rec_buf, fix_layout.home_team_id_offset, int(new_home_team_id))
            if new_away_team_id is not None:
                struct.pack_into("<I", rec_buf, fix_layout.away_team_id_offset, int(new_away_team_id))
            if new_date is not None or new_kick_off_time is not None:
                cur_d = decode_date(rec_buf, fix_layout.kick_off_date_offset) or prim_date
                existing_packed = read_u16(rec_buf, fix_layout.kick_off_date_offset)
                use_d = _coerce_date(new_date) or cur_d
                if use_d is not None:
                    pw, yr = encode_kick_off_words(
                        use_d,
                        new_kick_off_time,
                        fix_layout,
                        existing_packed_kick_off=existing_packed,
                    )
                    struct.pack_into("<HH", rec_buf, fix_layout.kick_off_date_offset, pw, yr)
            if new_played is not None:
                rec_buf[fix_layout.played_offset] = 1 if new_played else 0
            if new_round_index is not None:
                rec_buf[fix_layout.round_index_offset] = int(new_round_index) & 0xFF
            self.patch_span_bytes(base, rec_buf)
            updated_fixture_offsets.append(base)

        updated_results = 0
        if new_home_goals is not None or new_away_goals is not None:
            # 1. Update any RawStageResult in SPAN_REGION
            for sr in span_records.results:
                if (
                    sr.home_team_id == primary.home_team_id
                    and sr.away_team_id == primary.away_team_id
                    and (prim_date is None or sr.date == prim_date)
                ):
                    sr_buf = bytearray(self.read_span_bytes(sr.offset, res_layout.record_bytes))
                    if new_home_goals is not None:
                        sr_buf[res_layout.home_goals_offset] = int(new_home_goals) & 0xFF
                    if new_away_goals is not None:
                        sr_buf[res_layout.away_goals_offset] = int(new_away_goals) & 0xFF
                    self.patch_span_bytes(sr.offset, sr_buf)
                    updated_results += 1

            # 2. Update any StageResult in named result sections
            search = result_search(res_layout)
            for region_name in res_layout.regions:
                try:
                    sec_buf = self.get_section_buffer(region_name)
                except KeyError:
                    continue
                for m in search.pattern.finditer(bytes(sec_buf)):
                    r_start = m.start() - search.sentinel_offset
                    if r_start < 0 or r_start + res_layout.record_bytes > len(sec_buf):
                        continue
                    if sec_buf[r_start + res_layout.zero_byte_offset] != 0:
                        continue
                    h_id = read_u32(sec_buf, r_start + res_layout.home_team_id_offset)
                    a_id = read_u32(sec_buf, r_start + res_layout.away_team_id_offset)
                    r_d = decode_date(sec_buf, r_start + res_layout.date_offset)
                    if (
                        h_id == primary.home_team_id
                        and a_id == primary.away_team_id
                        and (prim_date is None or r_d == prim_date)
                    ):
                        if new_home_goals is not None:
                            sec_buf[r_start + res_layout.home_goals_offset] = int(new_home_goals) & 0xFF
                        if new_away_goals is not None:
                            sec_buf[r_start + res_layout.away_goals_offset] = int(new_away_goals) & 0xFF
                        updated_results += 1

            # 3. Update any MatchSummary in game_db.dat
            from fm26save._core.readers.match_summaries import _header_pattern, _sound_header

            db = self._game_db_buf()
            ms_layout: MatchSummaryLayout = self._layout(MatchSummaryLayout)
            ms_pat, ms_back = _header_pattern(ms_layout)
            start = 0
            while (hit := ms_pat.search(bytes(db), start)) is not None:
                start = hit.start() + 1
                at = hit.start() - ms_back
                if at < 0 or at + ms_layout.header_bytes > len(db) or not _sound_header(db, at, ms_layout):
                    continue
                count = db[at + ms_layout.count_offset]
                r_start = at + ms_layout.header_bytes
                if count > (len(db) - r_start) // ms_layout.record_bytes:
                    continue
                for _ in range(count):
                    if db[r_start + ms_layout.lead_byte_offset] != ms_layout.lead_byte_value:
                        break
                    h_id = read_u32(db, r_start + ms_layout.home_team_id_offset)
                    a_id = read_u32(db, r_start + ms_layout.away_team_id_offset)
                    m_d = decode_date(db, r_start + ms_layout.date_offset)
                    if (
                        h_id == primary.home_team_id
                        and a_id == primary.away_team_id
                        and (prim_date is None or m_d == prim_date)
                    ):
                        if new_home_goals is not None:
                            db[r_start + ms_layout.home_goals_offset] = int(new_home_goals) & 0xFF
                        if new_away_goals is not None:
                            db[r_start + ms_layout.away_goals_offset] = int(new_away_goals) & 0xFF
                        updated_results += 1
                    r_start += ms_layout.record_bytes

        rec = {
            "type": "edit_fixture",
            "home_team_id": primary.home_team_id,
            "away_team_id": primary.away_team_id,
            "date": str(prim_date),
            "updated_fixture_records": len(updated_fixture_offsets),
            "updated_result_records": updated_results,
            "new_home_goals": new_home_goals,
            "new_away_goals": new_away_goals,
        }
        self._edit_log.append(rec)
        return rec

    def edit_competition_rules(
        self,
        rules_block_index: int = 0,
        *,
        span_offset: int | None = None,
        promotion_places: int | None = None,
        playoff_places: int | None = None,
        promotion_byte2: int | None = None,
        relegation_places: int | None = None,
        prize_money: Sequence[int] | None = None,
        tie_breaks: Sequence[int] | None = None,
    ) -> dict[str, Any]:
        """Modify a competition-rules preamble block in `SPAN_REGION`.

        Writes both 4-byte copies of the promotion quad at `span_offset - 8` and `span_offset - 4`
        identically so `first_copy == second_copy` always holds.
        """
        rules_layout: RulesPreambleLayout = find_layout(
            RulesPreambleLayout, SPAN_REGION, None, self.version.build
        ).layout
        span_records = self._scan_span_records()
        blocks = span_records.rules_blocks
        if not blocks:
            raise RuntimeError("No competition rules blocks found in SPAN_REGION")

        target_block = None
        if span_offset is not None:
            for b in blocks:
                if b.span_offset == span_offset:
                    target_block = b
                    break
        else:
            idx = len(blocks) + rules_block_index if rules_block_index < 0 else rules_block_index
            if 0 <= idx < len(blocks):
                target_block = blocks[idx]
        if target_block is None:
            raise KeyError("Target competition rules block not found")

        mark = target_block.span_offset
        modified: dict[str, Any] = {"span_offset": mark}

        if any(
            x is not None
            for x in (promotion_places, playoff_places, promotion_byte2, relegation_places)
        ):
            quad_off = mark + rules_layout.promotion_quad_offset
            cur_quad = bytearray(self.read_span_bytes(quad_off, 4))
            if promotion_places is not None:
                cur_quad[0] = int(promotion_places) & 0xFF
            if playoff_places is not None:
                cur_quad[1] = int(playoff_places) & 0xFF
            if promotion_byte2 is not None:
                cur_quad[2] = int(promotion_byte2) & 0xFF
            if relegation_places is not None:
                cur_quad[3] = int(relegation_places) & 0xFF
            # Write twice back to back
            self.patch_span_bytes(quad_off, bytes(cur_quad) * 2)
            modified["promotion_quad"] = list(cur_quad)

        body_off = mark + rules_layout.body_offset
        tb_cnt = read_u32(self.read_span_bytes(body_off, 4), 0)
        if tie_breaks is not None:
            if len(tie_breaks) != tb_cnt:
                raise ValueError(
                    f"In-place tie_breaks update requires {tb_cnt} entries, got {len(tie_breaks)}"
                )
            tb_bytes = bytes(int(x) & 0xFF for x in tie_breaks)
            self.patch_span_bytes(body_off + 4, tb_bytes)
            modified["tie_breaks"] = list(tb_bytes)

        prize_off = body_off + 4 + tb_cnt
        pr_cnt = read_u32(self.read_span_bytes(prize_off, 4), 0)
        if prize_money is not None:
            if len(prize_money) != pr_cnt:
                raise ValueError(
                    f"In-place prize_money update requires {pr_cnt} entries, got {len(prize_money)}"
                )
            pr_bytes = struct.pack(f"<{pr_cnt}I", *(int(x) for x in prize_money))
            self.patch_span_bytes(prize_off + 4, pr_bytes)
            modified["prize_money"] = [int(x) for x in prize_money]

        self._edit_log.append({"type": "edit_competition_rules", **modified})
        return modified

    def edit_transfer_window(
        self,
        window_index: int,
        *,
        start_day: int | None = None,
        start_month: int | None = None,
        start_season_year_offset: int | None = None,
        end_day: int | None = None,
        end_month: int | None = None,
        end_season_year_offset: int | None = None,
        close_time: datetime.time | int | str | None = None,
        window_type: int | None = None,
    ) -> dict[str, Any]:
        """Modify a transfer window definition in `game_db.dat`'s tagged stream."""
        db = self._game_db_buf()
        stream_layout: TaggedStreamLayout = self._layout(TaggedStreamLayout)
        tw_layout: TransferWindowLayout = self._layout(TransferWindowLayout)

        hdr_bytes = stream_layout.tag_bytes + 2
        date_tags = (tw_layout.day_tag, tw_layout.month_tag, tw_layout.year_tag)
        windows_meta: list[dict[str, Any]] = []

        marker_offset = db.find(tw_layout.marker)
        while marker_offset >= 0:
            scan_end = min(marker_offset + tw_layout.window_scan_bytes, len(db))
            groups: dict[str, dict[str, tuple[int, int, int]]] = {}
            open_group: dict[str, tuple[int, int, int]] | None = None
            ct_info: tuple[int, int, int] | None = None
            wt_info: tuple[int, int, int] | None = None
            for tagged in iter_tagged_values(db, marker_offset, scan_end, stream_layout):
                tag = tagged.tag
                if tagged.kind == stream_layout.list_type and tag in (tw_layout.start_tag, tw_layout.end_tag):
                    open_group = {}
                    groups[tag] = open_group
                    continue
                val = tagged.value
                if not isinstance(val, int):
                    continue
                v_off = tagged.offset + hdr_bytes
                v_width = tagged.end - v_off
                if tag == tw_layout.window_type_tag:
                    wt_info = (val, v_off, v_width)
                elif tag == tw_layout.close_time_tag:
                    ct_info = (val, v_off, v_width)
                    break
                elif open_group is not None and tag in date_tags:
                    open_group[tag] = (val, v_off, v_width)

            if ct_info is not None:
                sg = groups.get(tw_layout.start_tag)
                eg = groups.get(tw_layout.end_tag)
                if sg and eg and all(k in sg for k in date_tags) and all(k in eg for k in date_tags):
                    s_d, s_m, s_y = sg[tw_layout.day_tag][0], sg[tw_layout.month_tag][0], sg[tw_layout.year_tag][0]
                    e_d, e_m, e_y = eg[tw_layout.day_tag][0], eg[tw_layout.month_tag][0], eg[tw_layout.year_tag][0]
                    ld, hd = tw_layout.day_range
                    lm, hm = tw_layout.month_range
                    ly, hy = tw_layout.year_range
                    if (
                        ld <= s_d <= hd and lm <= s_m <= hm and ly <= s_y <= hy
                        and ld <= e_d <= hd and lm <= e_m <= hm and ly <= e_y <= hy
                    ):
                        windows_meta.append({
                            "marker_offset": marker_offset,
                            "start": sg,
                            "end": eg,
                            "close_time": ct_info,
                            "window_type": wt_info,
                        })
            marker_offset = db.find(tw_layout.marker, marker_offset + 1)

        idx = len(windows_meta) + window_index if window_index < 0 else window_index
        if not 0 <= idx < len(windows_meta):
            raise IndexError(f"Transfer window index {window_index} out of range (0..{len(windows_meta) - 1})")

        w = windows_meta[idx]
        modified: dict[str, Any] = {"window_index": idx, "offset": w["marker_offset"]}

        def _write_tagged_int(info: tuple[int, int, int], new_val: int) -> None:
            _old, v_off, v_width = info
            db[v_off : v_off + v_width] = int(new_val).to_bytes(v_width, "little", signed=False)

        if start_day is not None:
            _write_tagged_int(w["start"][tw_layout.day_tag], int(start_day))
            modified["start_day"] = int(start_day)
        if start_month is not None:
            _write_tagged_int(w["start"][tw_layout.month_tag], int(start_month))
            modified["start_month"] = int(start_month)
        if start_season_year_offset is not None:
            _write_tagged_int(
                w["start"][tw_layout.year_tag],
                tw_layout.season_year_base + int(start_season_year_offset),
            )
            modified["start_season_year_offset"] = int(start_season_year_offset)
        if end_day is not None:
            _write_tagged_int(w["end"][tw_layout.day_tag], int(end_day))
            modified["end_day"] = int(end_day)
        if end_month is not None:
            _write_tagged_int(w["end"][tw_layout.month_tag], int(end_month))
            modified["end_month"] = int(end_month)
        if end_season_year_offset is not None:
            _write_tagged_int(
                w["end"][tw_layout.year_tag],
                tw_layout.season_year_base + int(end_season_year_offset),
            )
            modified["end_season_year_offset"] = int(end_season_year_offset)
        if close_time is not None:
            if isinstance(close_time, int):
                ct_val = close_time
            else:
                t = _coerce_time(close_time)
                ct_val = (t.hour * 60 + t.minute) if t is not None else 0
            _write_tagged_int(w["close_time"], ct_val)
            modified["close_time"] = ct_val
        if window_type is not None and w["window_type"] is not None:
            _write_tagged_int(w["window_type"], int(window_type))
            modified["window_type"] = int(window_type)

        self._edit_log.append({"type": "edit_transfer_window", **modified})
        return modified

    def edit_player_match_stat(
        self,
        player_uid_or_name: int | str,
        match_index: int = 0,
        *,
        goals: int | None = None,
        assists: int | None = None,
        minutes: int | None = None,
        rating: float | None = None,
        passes_attempted: int | None = None,
        passes_completed: int | None = None,
        position_mask: int | None = None,
        role_code: int | None = None,
        match_date: datetime.date | str | None = None,
        opponent_team_id: int | None = None,
        competition_id: int | None = None,
    ) -> dict[str, Any]:
        """Modify a player's per-match performance record (`MatchRecordLayout`) in `game_db.dat`."""
        from fm26save._core.readers.matches import _match_search, _read_match_record

        db = self._game_db_buf()
        mr_layout: MatchRecordLayout = self._layout(MatchRecordLayout)
        prec = self._player_records()
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        clock = self._save_reader.info.game_date or datetime.date(2025, 8, 1)
        search = _match_search(mr_layout, clock.year)

        owned_start = max(0, rec_off - search.owner_back_offset)
        owned_end = (
            prec.record_offsets[pos_idx + 1] - search.owner_back_offset
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )

        record_offsets: list[int] = []
        cursor = owned_start
        while (hit := search.parent_pattern.search(bytes(db), cursor, owned_end)) is not None:
            parent_at = hit.start()
            cursor = parent_at + 1
            list_at = parent_at + mr_layout.parent_header_bytes
            child_count = db[parent_at + mr_layout.parent_count_offset]
            for _ in range(child_count):
                if (
                    list_at + search.list_header_bytes > owned_end
                    or bytes(db[list_at : list_at + 2]) not in mr_layout.list_markers
                ):
                    break
                _team, count = search.list_header_struct.unpack_from(db, list_at)
                at = list_at + search.list_header_bytes
                for _ in range(count):
                    decoded = _read_match_record(db, at, search, owned_end)
                    if decoded is None:
                        break
                    rec_obj, size = decoded
                    if rec_obj.has_stats:
                        record_offsets.append(at)
                    at += size
                list_at = at

        if not record_offsets:
            raise KeyError(f"No match stat records with body found in game_db for player {uid}")
        idx = len(record_offsets) + match_index if match_index < 0 else match_index
        if not 0 <= idx < len(record_offsets):
            raise IndexError(f"match_index {match_index} out of range (0..{len(record_offsets) - 1})")

        r_off = record_offsets[idx]
        modified: dict[str, Any] = {"uid": uid, "match_index": idx, "offset": r_off}
        if goals is not None:
            db[r_off + mr_layout.goals_offset] = int(goals) & 0xFF
            modified["goals"] = int(goals)
        if assists is not None:
            db[r_off + mr_layout.assists_offset] = int(assists) & 0xFF
            modified["assists"] = int(assists)
        if minutes is not None:
            db[r_off + mr_layout.minutes_offset] = min(mr_layout.maximum_minutes, max(0, int(minutes))) & 0xFF
            modified["minutes"] = int(minutes)
        if rating is not None:
            raw_r = min(mr_layout.maximum_rating, max(1, int(round(float(rating) * mr_layout.rating_scale))))
            db[r_off + mr_layout.rating_offset] = raw_r
            modified["rating"] = raw_r / mr_layout.rating_scale
        if passes_attempted is not None:
            db[r_off + mr_layout.passes_attempted_offset] = int(passes_attempted) & 0xFF
            modified["passes_attempted"] = int(passes_attempted)
        if passes_completed is not None:
            db[r_off + mr_layout.passes_completed_offset] = int(passes_completed) & 0xFF
            modified["passes_completed"] = int(passes_completed)
        pa_val = db[r_off + mr_layout.passes_attempted_offset]
        pc_val = db[r_off + mr_layout.passes_completed_offset]
        if pc_val > pa_val:
            db[r_off + mr_layout.passes_attempted_offset] = pc_val
        if position_mask is not None:
            struct.pack_into("<H", db, r_off + mr_layout.position_mask_offset, int(position_mask) & 0xFFFF)
            modified["position_mask"] = int(position_mask)
        if role_code is not None:
            db[r_off + mr_layout.role_code_offset] = int(role_code) & 0xFF
            modified["role_code"] = int(role_code)
        if match_date is not None:
            write_packed_date_into(db, r_off + mr_layout.date_offset, match_date)
            modified["date"] = str(_coerce_date(match_date))
        if opponent_team_id is not None:
            struct.pack_into("<I", db, r_off + mr_layout.opponent_team_id_offset, int(opponent_team_id))
            modified["opponent_team_id"] = int(opponent_team_id)
        if competition_id is not None:
            struct.pack_into("<I", db, r_off + mr_layout.competition_id_offset, int(competition_id))
            modified["competition_id"] = int(competition_id)

        self._edit_log.append({"type": "edit_player_match_stat", **modified})
        return modified

    def edit_player_season_stats(
        self,
        player_uid_or_name: int | str,
        *,
        slot: str | int = "league",
        start_appearances: int | None = None,
        sub_appearances: int | None = None,
        goals: int | None = None,
        assists: int | None = None,
        yellow_cards: int | None = None,
        red_cards: int | None = None,
        player_of_the_match: int | None = None,
        penalties_taken: int | None = None,
        penalties_scored: int | None = None,
        rating_hundredths: int | None = None,
        minutes: int | None = None,
        passes_attempted: int | None = None,
        passes_completed: int | None = None,
        recompute_overall: bool = True,
    ) -> dict[str, Any]:
        """Modify a player's current-season statistics in the unlisted season-statistics span frame.

        Automatically maintains `overall == league + cup + continental` (`starts`, `substitute_appearances`,
        `minutes`, `goals`, `assists`) and `penalties_scored <= penalties_taken`, `passes_completed <= passes_attempted`.
        """
        from fm26save._core.readers.season_stats import _section_header, walk_season_stats

        ss_layout: SeasonStatsLayout = find_layout(
            SeasonStatsLayout, SPAN_REGION, None, self.version.build
        ).layout
        prec = self._player_records()
        pos_idx, _rec_off, uid = self._resolve_player_position(player_uid_or_name)
        player_key = int(prec.pindexes[pos_idx]) + 1

        slot_kinds = list(ss_layout.slot_kinds)
        if isinstance(slot, int):
            slot_idx = slot
        else:
            s_norm = slot.strip().lower()
            if s_norm in slot_kinds:
                slot_idx = slot_kinds.index(s_norm)
            elif s_norm.startswith("slot_"):
                slot_idx = int(s_norm.split("_", 1)[1])
            else:
                raise ValueError(f"Unknown season stats slot {slot!r}")
        if not 0 <= slot_idx < ss_layout.own_slots:
            raise ValueError(f"Slot index {slot_idx} out of range (0..{ss_layout.own_slots - 1})")

        header = _section_header(ss_layout)
        target_buf: bytearray | None = None
        walk = None
        for _s, _e, entry in self._rgman_intervals():
            buf = self._get_entry_buffer(entry)
            if bytes(buf[: len(header)]) == header:
                try:
                    walk = walk_season_stats(bytes(buf), ss_layout, self.source_path.name)
                    target_buf = buf
                    break
                except Exception:
                    continue

        if target_buf is None or walk is None:
            raise RuntimeError("Season statistics frame not found in SPAN_REGION")

        target_rec = next((r for r in walk.records if r.key == player_key), None)
        if target_rec is None:
            raise KeyError(f"SeasonStats record not found for player {uid} (key={player_key})")

        line_off = target_rec.own_lines[slot_idx]
        if line_off is None:
            # Find any existing line in own_lines to fallback if the requested slot is absent
            line_off = next((off for off in target_rec.own_lines if off is not None), None)
            if line_off is None:
                raise KeyError(f"Player {uid} has no active season statistics lines to edit in-place")
            slot_idx = target_rec.own_lines.index(line_off)

        f_map = {name: (off, fmt) for name, off, fmt, _unit in ss_layout.fields}

        def _read_f(l_off: int, name: str) -> int:
            off, fmt = f_map[name]
            return int(struct.unpack_from("<" + fmt, target_buf, l_off + off)[0])

        def _write_f(l_off: int, name: str, val: int) -> None:
            off, fmt = f_map[name]
            max_v = 255 if fmt == "B" else 65535
            struct.pack_into("<" + fmt, target_buf, l_off + off, max(0, min(max_v, int(val))))

        if start_appearances is not None:
            _write_f(line_off, "starts", start_appearances)
        if sub_appearances is not None:
            _write_f(line_off, "substitute_appearances", sub_appearances)
        if goals is not None:
            _write_f(line_off, "goals", goals)
        if assists is not None:
            _write_f(line_off, "assists", assists)
        if yellow_cards is not None:
            _write_f(line_off, "yellow_cards", yellow_cards)
        if red_cards is not None:
            _write_f(line_off, "red_cards", red_cards)
        if player_of_the_match is not None:
            _write_f(line_off, "player_of_the_match", player_of_the_match)
        if penalties_taken is not None:
            _write_f(line_off, "penalties_taken", penalties_taken)
        if penalties_scored is not None:
            _write_f(line_off, "penalties_scored", penalties_scored)
        if _read_f(line_off, "penalties_scored") > _read_f(line_off, "penalties_taken"):
            _write_f(line_off, "penalties_taken", _read_f(line_off, "penalties_scored"))

        if rating_hundredths is not None:
            struct.pack_into(
                "<H", target_buf, line_off + ss_layout.rating_sum_offset, int(rating_hundredths) & 0xFFFF
            )
        if minutes is not None:
            _write_f(line_off, "minutes", minutes)
        # Ensure minutes <= maximum_minutes_per_appearance * (starts + substitute_appearances)
        apps = _read_f(line_off, "starts") + _read_f(line_off, "substitute_appearances")
        if _read_f(line_off, "minutes") > ss_layout.maximum_minutes_per_appearance * apps:
            if apps == 0:
                _write_f(line_off, "starts", max(1, (_read_f(line_off, "minutes") + 89) // 90))
                apps = _read_f(line_off, "starts")
            _write_f(line_off, "minutes", min(_read_f(line_off, "minutes"), ss_layout.maximum_minutes_per_appearance * apps))

        if passes_attempted is not None:
            _write_f(line_off, "passes_attempted", passes_attempted)
        if passes_completed is not None:
            _write_f(line_off, "passes_completed", passes_completed)
        if _read_f(line_off, "passes_completed") > _read_f(line_off, "passes_attempted"):
            _write_f(line_off, "passes_attempted", _read_f(line_off, "passes_completed"))

        comp_slots = tuple(slot_kinds.index(k) for k in ("league", "cup", "continental") if k in slot_kinds)
        overall_slot = slot_kinds.index("overall") if "overall" in slot_kinds else -1
        if recompute_overall and overall_slot >= 0 and slot_idx in comp_slots:
            ov_off = target_rec.own_lines[overall_slot]
            if ov_off is not None:
                for sum_field in ("starts", "substitute_appearances", "minutes", "goals", "assists"):
                    total_v = sum(
                        _read_f(target_rec.own_lines[cs], sum_field)
                        for cs in comp_slots
                        if target_rec.own_lines[cs] is not None
                    )
                    _write_f(ov_off, sum_field, total_v)

        rec = {
            "type": "edit_player_season_stats",
            "uid": uid,
            "slot": slot_idx,
            "start_appearances": _read_f(line_off, "starts"),
            "sub_appearances": _read_f(line_off, "substitute_appearances"),
            "goals": _read_f(line_off, "goals"),
            "assists": _read_f(line_off, "assists"),
            "minutes": _read_f(line_off, "minutes"),
        }
        self._edit_log.append(rec)
        return rec

    def edit_player_season_history(
        self,
        player_uid_or_name: int | str,
        row_index: int = -1,
        *,
        season_start_year: int | None = None,
        team_id: int | None = None,
        appearances: int | None = None,
        goals: int | None = None,
        kind: int | None = None,
    ) -> dict[str, Any]:
        """Modify a player's career season history row in `player_stats_hist_dt.dat`."""
        from fm26save._core.readers.season_history import history_selector, walk_history_index

        hist_buf = self.get_section_buffer(SEASON_HISTORY_SECTION)
        sh_layout: SeasonHistoryLayout = find_layout(
            SeasonHistoryLayout, SPAN_REGION, None, self.version.build
        ).layout
        db = self._game_db_buf()
        prec = self._player_records()
        person_layout = self._layout(PersonBlockLayout)
        pos_idx, rec_off, uid = self._resolve_player_position(player_uid_or_name)
        next_rec_off = (
            prec.record_offsets[pos_idx + 1]
            if pos_idx + 1 < len(prec.record_offsets)
            else len(db)
        )
        clock_yr = (self.get_game_date() or datetime.date(2050, 1, 1)).year
        pblock = locate_person_block(
            db,
            rec_off + person_layout.window_start_offset,
            next_rec_off,
            person_layout,
            clock_year=clock_yr,
        )
        block_start = (
            pblock.birth_date_offset + pblock.name_block_offset_from_birth
            if pblock is not None and pblock.has_name_block
            else None
        )
        selector = history_selector(db, block_start, rec_off, next_rec_off, sh_layout)
        if selector == 0xFFFFFFFF:
            raise KeyError(f"Player {uid} has no season history selector in game_db.dat")

        # Locate the history index frame in SPAN_REGION
        hist_idx = None
        for _s, _e, entry in self._rgman_intervals():
            buf = self._get_entry_buffer(entry)
            if bytes(buf[: len(sh_layout.index_header)]) == sh_layout.index_header:
                try:
                    hist_idx = walk_history_index(bytes(buf), self.source_path.name, sh_layout)
                    break
                except Exception:
                    continue
        if hist_idx is None:
            raise RuntimeError("History index frame not found in SPAN_REGION")
        if not 0 <= selector < len(hist_idx.lists) or not hist_idx.lists[selector]:
            raise KeyError(f"Player {uid} has an empty season history list (selector={selector})")

        unit_offsets = hist_idx.lists[selector]
        idx = len(unit_offsets) + row_index if row_index < 0 else row_index
        if not 0 <= idx < len(unit_offsets):
            raise IndexError(f"row_index {row_index} out of range (0..{len(unit_offsets) - 1})")

        at = len(sh_layout.archive_header) + unit_offsets[idx]
        modified: dict[str, Any] = {"uid": uid, "row_index": idx, "offset": at}
        # Metadata at `at + 1` is `<IHIH`: (team_id, competition, unknown, year)
        if team_id is not None:
            struct.pack_into("<I", hist_buf, at + 1, int(team_id))
            modified["team_id"] = int(team_id)
        if season_start_year is not None:
            struct.pack_into("<H", hist_buf, at + 1 + 10, int(season_start_year) & 0xFFFF)
            modified["season_start_year"] = int(season_start_year)
        if appearances is not None:
            # `starts` is at `at + 24`, `substitute_appearances` at `at + 25`
            hist_buf[at + 24] = min(254, max(0, int(appearances)))
            modified["appearances"] = int(appearances)
        if goals is not None:
            # `goals` is at `at + 27`
            hist_buf[at + 27] = min(254, max(0, int(goals)))
            modified["goals"] = int(goals)
        if kind is not None:
            hist_buf[at + 31] = max(0, min(len(sh_layout.kind_names) - 1, int(kind)))
            modified["kind"] = int(kind)

        self._edit_log.append({"type": "edit_player_season_history", **modified})
        return modified

    # ------------------------------------------------------------------
    # 9. Extra Container Sections (`extra_sections.py`)
    # ------------------------------------------------------------------
    def edit_hall_of_fame_entry(
        self,
        entry_index: int = 0,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        common_name: str | None = None,
        birth_date: datetime.date | str | None = None,
        manager_uid: int | None = None,
        nation_uid: int | None = None,
        hall_of_fame_points: int | None = None,
    ) -> dict[str, Any]:
        """Modify a manager trophy/points entry in `hall_of_fame.dat`."""
        from fm26save.extra_sections import _read_lp_utf8

        buf = self.get_section_buffer("hall_of_fame.dat")
        raw = bytes(buf)
        entries: list[dict[str, int]] = []
        pos = 8
        end = len(raw) - 24
        while pos < end and len(entries) < 500:
            if raw[pos] == 1:
                fn, next1 = _read_lp_utf8(raw, pos + 1, 45)
                if fn and len(fn) >= 2 and any(c.isalpha() for c in fn):
                    ln, next2 = _read_lp_utf8(raw, next1, 45)
                    if ln and len(ln) >= 2 and any(c.isalpha() for c in ln):
                        cn, next3 = _read_lp_utf8(raw, next2, 45)
                        if cn is not None and next3 + 22 <= len(raw):
                            b_date = decode_date(raw, next3)
                            if b_date is not None and 1900 <= b_date.year <= 2045:
                                n_entries = raw[next3 + 17]
                                epos = next3 + 18
                                valid_walk = True
                                for _ in range(n_entries):
                                    if epos + 24 > len(raw) or raw[epos : epos + 2] != b"\x03\x03":
                                        valid_walk = False
                                        break
                                    ycnt = struct.unpack_from("<H", raw, epos + 22)[0]
                                    if ycnt > 200 or epos + 24 + 4 * ycnt > len(raw):
                                        valid_walk = False
                                        break
                                    epos += 24 + 4 * ycnt
                                entries.append(
                                    {
                                        "pos": pos,
                                        "next1": next1,
                                        "next2": next2,
                                        "next3": next3,
                                        "points_off": epos if (valid_walk and epos + 4 <= len(raw)) else -1,
                                    }
                                )
                                pos = epos + 4 if (valid_walk and epos > next3) else next3 + 22
                                continue
            pos += 1

        idx = len(entries) + entry_index if entry_index < 0 else entry_index
        if not 0 <= idx < len(entries):
            raise IndexError(f"Hall of Fame entry index {entry_index} out of range (0..{len(entries) - 1})")

        info = entries[idx]
        next3 = info["next3"]
        modified: dict[str, Any] = {"entry_index": idx, "offset": info["pos"]}
        if birth_date is not None:
            write_packed_date_into(buf, next3, birth_date)
            modified["birth_date"] = str(_coerce_date(birth_date))
        if manager_uid is not None:
            struct.pack_into("<i", buf, next3 + 8, int(manager_uid))
            modified["manager_uid"] = int(manager_uid)
        if nation_uid is not None:
            struct.pack_into("<i", buf, next3 + 13, int(nation_uid))
            modified["nation_uid"] = int(nation_uid)
        if hall_of_fame_points is not None and info["points_off"] >= 0:
            struct.pack_into("<I", buf, info["points_off"], int(hall_of_fame_points))
            modified["hall_of_fame_points"] = int(hall_of_fame_points)

        # Apply variable-length string edits in reverse offset order so earlier offsets stay valid
        if common_name is not None:
            cb = common_name.encode("utf-8")
            buf[info["next2"] : info["next3"]] = struct.pack("<I", len(cb)) + cb
            modified["common_name"] = common_name
        if last_name is not None:
            lb = last_name.encode("utf-8")
            buf[info["next1"] : info["next2"]] = struct.pack("<I", len(lb)) + lb
            modified["last_name"] = last_name
        if first_name is not None:
            fb = first_name.encode("utf-8")
            buf[info["pos"] + 1 : info["next1"]] = struct.pack("<I", len(fb)) + fb
            modified["first_name"] = first_name

        self._edit_log.append({"type": "edit_hall_of_fame_entry", **modified})
        return modified

    def edit_board_takeover(
        self,
        record_index: int = 0,
        *,
        investor_first_name: str | None = None,
        investor_last_name: str | None = None,
        nation_id: int | None = None,
        club_uid_or_name: int | str | None = None,
    ) -> dict[str, Any]:
        """Modify an investor / board takeover record in `board_takeover_manager.dat`."""
        from fm26save.extra_sections import _read_lp_utf8

        try:
            buf = self.get_section_buffer("board_takeover_manager.dat")
        except KeyError:
            buf = self.get_section_buffer("board_takeover_man.dat")

        raw = bytes(buf)
        entries: list[dict[str, int]] = []
        pos = 8
        end = len(raw) - 20
        while pos < end:
            if raw[pos : pos + 3] == b"\x08\x01\x0b":
                fn, next1 = _read_lp_utf8(raw, pos + 3, 45)
                if fn and len(fn) >= 2:
                    ln, next2 = _read_lp_utf8(raw, next1, 45)
                    if ln and len(ln) >= 2:
                        cn, next3 = _read_lp_utf8(raw, next2, 45)
                        if cn is not None:
                            entries.append(
                                {"pos": pos, "next1": next1, "next2": next2, "next3": next3}
                            )
                            pos = next3
                            continue
            pos += 1

        idx = len(entries) + record_index if record_index < 0 else record_index
        if not 0 <= idx < len(entries):
            raise IndexError(f"Board takeover index {record_index} out of range (0..{len(entries) - 1})")

        info = entries[idx]
        p_off = info["pos"]
        modified: dict[str, Any] = {"record_index": idx, "offset": p_off}
        if club_uid_or_name is not None and p_off >= 52:
            club = self._resolve_club_record(club_uid_or_name)
            c_idx_val = self._club_index_for_uid(club.uid)
            struct.pack_into("<I", buf, p_off - 51, max(0, c_idx_val - 1))
            if nation_id is None and not (1 <= read_u32(buf, p_off - 47) <= 250):
                struct.pack_into("<I", buf, p_off - 47, int(club.nation_id or 1))
            modified["club_uid"] = club.uid
        if nation_id is not None and p_off >= 52:
            struct.pack_into("<I", buf, p_off - 47, int(nation_id))
            modified["nation_id"] = int(nation_id)
        if investor_last_name is not None:
            lb = investor_last_name.encode("utf-8")
            buf[info["next1"] : info["next2"]] = struct.pack("<I", len(lb)) + lb
            modified["investor_last_name"] = investor_last_name
        if investor_first_name is not None:
            fb = investor_first_name.encode("utf-8")
            buf[p_off + 3 : info["next1"]] = struct.pack("<I", len(fb)) + fb
            modified["investor_first_name"] = investor_first_name

        self._edit_log.append({"type": "edit_board_takeover", **modified})
        return modified

    def edit_shortlist_slot(
        self,
        slot_index: int = 0,
        *,
        player_uid_or_name: int | str | None = None,
        score_or_priority: int | None = None,
    ) -> dict[str, Any]:
        """Modify a tracked/shortlisted player slot in `shortlist_man.dat`."""
        buf = self.get_section_buffer("shortlist_man.dat")
        if len(buf) < 16:
            raise RuntimeError("shortlist_man.dat too short")
        declared_count = read_u32(buf, 8)
        max_items = min(declared_count, (len(buf) - 12) // 8)
        idx = max_items + slot_index if slot_index < 0 else slot_index
        if not 0 <= idx < max_items:
            raise IndexError(f"Shortlist slot {slot_index} out of range (0..{max_items - 1})")

        off = 12 + idx * 8
        val_a, val_b = struct.unpack_from("<II", buf, off)
        prec = self._player_records()
        # Determine which word holds the player selector
        sel_in_b = (val_b - 1) in prec.position_by_pindex
        modified: dict[str, Any] = {"slot_index": idx, "offset": off}

        if player_uid_or_name is not None:
            pos_idx, _ro, uid = self._resolve_player_position(player_uid_or_name)
            new_sel = prec.pindexes[pos_idx] + 1
            if sel_in_b:
                val_b = new_sel
            else:
                val_a = new_sel
            modified["player_uid"] = uid
            modified["selector"] = new_sel
        if score_or_priority is not None:
            if sel_in_b:
                val_a = int(score_or_priority)
            else:
                val_b = int(score_or_priority)
            modified["score_or_priority"] = int(score_or_priority)

        struct.pack_into("<II", buf, off, val_a, val_b)
        self._edit_log.append({"type": "edit_shortlist_slot", **modified})
        return modified

    def edit_contract_offer(
        self,
        offer_index: int = 0,
        *,
        player_uid_or_name: int | str | None = None,
        event_date: datetime.date | str | None = None,
    ) -> dict[str, Any]:
        """Modify an active contract negotiation / event entry in `contract_man.dat`."""
        buf = self.get_section_buffer("contract_man.dat")
        if len(buf) < 12:
            raise RuntimeError("contract_man.dat too short")
        count = read_u32(buf, 8)
        max_items = min(count, (len(buf) - 12) // 8)
        idx = max_items + offer_index if offer_index < 0 else offer_index
        if not 0 <= idx < max_items:
            raise IndexError(f"Contract offer index {offer_index} out of range (0..{max_items - 1})")

        off = 12 + idx * 8
        modified: dict[str, Any] = {"offer_index": idx, "offset": off}
        if player_uid_or_name is not None:
            prec = self._player_records()
            pos_idx, _ro, uid = self._resolve_player_position(player_uid_or_name)
            new_sel = prec.pindexes[pos_idx] + 1
            struct.pack_into("<I", buf, off, new_sel)
            modified["player_uid"] = uid
            modified["selector"] = new_sel
        if event_date is not None:
            write_packed_date_into(buf, off + 4, event_date)
            modified["event_date"] = str(_coerce_date(event_date))

        self._edit_log.append({"type": "edit_contract_offer", **modified})
        return modified

    def edit_agent_slot(
        self,
        slot_index: int = 0,
        *,
        agent_person_selector: int,
    ) -> dict[str, Any]:
        """Modify a registered agent person selector in `agent_manager.dat`."""
        buf = self.get_section_buffer("agent_manager.dat")
        if len(buf) < 12:
            raise RuntimeError("agent_manager.dat too short")
        count = read_u32(buf, 8)
        max_items = min(count, (len(buf) - 12) // 4)
        idx = max_items + slot_index if slot_index < 0 else slot_index
        if not 0 <= idx < max_items:
            raise IndexError(f"Agent slot index {slot_index} out of range (0..{max_items - 1})")

        off = 12 + idx * 4
        struct.pack_into("<I", buf, off, int(agent_person_selector))
        rec = {
            "type": "edit_agent_slot",
            "slot_index": idx,
            "offset": off,
            "agent_person_selector": int(agent_person_selector),
        }
        self._edit_log.append(rec)
        return rec

    def edit_news_headline(
        self,
        old_text: str,
        new_text: str,
    ) -> dict[str, Any]:
        """Replace a length-prefixed UTF-8 news headline/string in `news.dat`."""
        buf = self.get_section_buffer("news.dat")
        old_b = old_text.encode("utf-8")
        pattern = struct.pack("<I", len(old_b)) + old_b
        hit = buf.find(pattern)
        if hit < 0:
            raise KeyError(f"News string {old_text!r} not found in news.dat")
        new_b = new_text.encode("utf-8")
        buf[hit : hit + len(pattern)] = struct.pack("<I", len(new_b)) + new_b
        rec = {
            "type": "edit_news_headline",
            "offset": hit,
            "old_text": old_text,
            "new_text": new_text,
        }
        self._edit_log.append(rec)
        return rec

