"""Low-level TADF + Zstandard FM26 Save Container Reader and Section Extractor."""

from __future__ import annotations

import hashlib
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fm26save._core._container import (
    ContainerIndex,
    DirectoryEntry,
    match_file_entries,
    read_directory_entry,
    read_index,
    read_section,
)


@dataclass(frozen=True, slots=True)
class RawSectionSummary:
    """Metadata and summary of a single Zstandard section or match file inside the save."""

    name: str
    extension: str
    full_name: str
    frame_offset: int
    compressed_size: int
    decompressed_size: int
    compression_ratio: float
    is_section: bool
    trailing_values: tuple[int, int]


class FM26Container:
    """Direct reader for the 81+ Zstandard sections and match files inside an .fm save."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.index: ContainerIndex = read_index(self.path)

    def list_entries(self) -> list[RawSectionSummary]:
        """Return every entry (both .dat/.cmt sections and .apm/.scm match files) in directory order."""
        out: list[RawSectionSummary] = []
        for entry in self.index.entries:
            ratio = (
                round(entry.decompressed_size / entry.compressed_size, 2)
                if entry.compressed_size > 0
                else 0.0
            )
            out.append(
                RawSectionSummary(
                    name=entry.name,
                    extension=entry.extension,
                    full_name=f"{entry.name}{entry.extension}",
                    frame_offset=entry.frame_offset,
                    compressed_size=entry.compressed_size,
                    decompressed_size=entry.decompressed_size,
                    compression_ratio=ratio,
                    is_section=entry.is_section,
                    trailing_values=entry.trailing_values,
                )
            )
        return out

    def list_match_files(self) -> list[DirectoryEntry]:
        """Return embedded .apm / .scm match record files in the container."""
        return list(match_file_entries(self.index))

    def read_raw(self, name: str) -> bytes:
        """Decompress and return raw bytes of a section by name (with or without .dat/.cmt extension)."""
        clean_name = name
        if clean_name.endswith((".dat", ".cmt", ".apm", ".scm")):
            clean_name = clean_name[:-4]
        entry = self.index.sections.get(clean_name)
        if entry is None:
            for item in self.index.entries:
                if item.name == clean_name or f"{item.name}{item.extension}" == name:
                    entry = item
                    break
        if entry is not None:
            return read_directory_entry(self.index, entry)
        return read_section(self.index, clean_name)

    def section_sha256(self, name: str) -> str:
        """Return SHA-256 hex digest of a decompressed section."""
        return hashlib.sha256(self.read_raw(name)).hexdigest()

    def unpack_all(self, output_dir: str | os.PathLike[str], *, skip_game_db: bool = False) -> list[dict[str, Any]]:
        """Decompress and write all sections to disk as .bin files."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest: list[dict[str, Any]] = []
        for entry in self.list_entries():
            if skip_game_db and entry.name == "game_db":
                continue
            raw = self.read_raw(entry.name)
            target = out_path / f"{entry.full_name}.bin"
            target.write_bytes(raw)
            manifest.append(
                {
                    "section": entry.full_name,
                    "compressed_size": entry.compressed_size,
                    "decompressed_size": len(raw),
                    "output_file": str(target),
                }
            )
        return manifest


def extract_length_prefixed_strings(
    data: bytes,
    *,
    min_len: int = 3,
    max_len: int = 80,
    max_scan_bytes: int = 2_000_000,
    max_results: int = 500,
) -> list[dict[str, Any]]:
    """Scan binary buffer for length-prefixed (<I length + UTF-8) readable strings."""
    results: list[dict[str, Any]] = []
    pos = 0
    limit = min(len(data) - 6, max_scan_bytes)
    unpack_u32 = struct.Struct("<I").unpack_from
    while pos < limit and len(results) < max_results:
        ln = unpack_u32(data, pos)[0]
        if min_len <= ln <= max_len and pos + 4 + ln <= len(data):
            chunk = data[pos + 4 : pos + 4 + ln]
            if all(32 <= b < 127 or b >= 128 for b in chunk):
                try:
                    text = chunk.decode("utf-8")
                    valid_chars = sum(c.isalnum() or c in " ._-/()'’," for c in text)
                    if any(c.isalpha() for c in text) and valid_chars >= len(text) * 0.85:
                        results.append({"offset": pos, "length": ln, "text": text})
                        pos += 4 + ln
                        continue
                except UnicodeDecodeError:
                    pass
        pos += 1
    return results
