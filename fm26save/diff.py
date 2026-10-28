"""Binary and Section-Level Save Diff Engine for FM26 Save Reverse-Engineering."""

from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path
from typing import Any

from fm26save import _core
from fm26save.container import FM26Container


def _find_byte_diff_runs(
    bytes_a: bytes,
    bytes_b: bytes,
    *,
    max_runs: int = 100,
    merge_gap: int = 4,
) -> list[dict[str, Any]]:
    """Find contiguous runs of differing bytes between two buffers."""
    min_len = min(len(bytes_a), len(bytes_b))
    runs: list[tuple[int, int]] = []
    i = 0
    while i < min_len and len(runs) < max_runs:
        if bytes_a[i] != bytes_b[i]:
            start = i
            i += 1
            while i < min_len:
                if bytes_a[i] != bytes_b[i]:
                    i += 1
                else:
                    # Check if another diff occurs within merge_gap bytes
                    next_diff = -1
                    for g in range(1, min(merge_gap + 1, min_len - i)):
                        if bytes_a[i + g] != bytes_b[i + g]:
                            next_diff = i + g
                            break
                    if next_diff >= 0:
                        i = next_diff + 1
                    else:
                        break
            runs.append((start, min(i, start + 64)))
        else:
            i += 1

    detailed: list[dict[str, Any]] = []
    for start, end in runs:
        chunk_a = bytes_a[start:end]
        chunk_b = bytes_b[start:end]
        item: dict[str, Any] = {
            "offset": start,
            "offset_hex": f"0x{start:06X}",
            "length": end - start,
            "old_hex": chunk_a.hex(" "),
            "new_hex": chunk_b.hex(" "),
            "old_bytes": list(chunk_a[:16]),
            "new_bytes": list(chunk_b[:16]),
        }
        if start + 4 <= min_len:
            item["old_u32"] = struct.unpack_from("<I", bytes_a, start)[0]
            item["new_u32"] = struct.unpack_from("<I", bytes_b, start)[0]
        if start + 2 <= min_len:
            item["old_u16"] = struct.unpack_from("<H", bytes_a, start)[0]
            item["new_u16"] = struct.unpack_from("<H", bytes_b, start)[0]
        detailed.append(item)
    return detailed


def diff_saves(
    path_a: str | os.PathLike[str],
    path_b: str | os.PathLike[str],
    *,
    deep_diff_max_section_bytes: int = 25_000_000,
    specific_section: str | None = None,
    max_runs_per_section: int = 50,
) -> dict[str, Any]:
    """Compare two FM26 .fm saves across all 81 Zstandard sections and return byte-level diffs."""
    cont_a = FM26Container(path_a)
    cont_b = FM26Container(path_b)

    with _core.open(path_a) as sa, _core.open(path_b) as sb:
        info_a = sa.info
        info_b = sb.info

    entries_a = {e.full_name: e for e in cont_a.list_entries() if e.is_section}
    entries_b = {e.full_name: e for e in cont_b.list_entries() if e.is_section}

    all_names = sorted(set(entries_a) | set(entries_b))
    if specific_section:
        clean = specific_section if specific_section.endswith((".dat", ".cmt")) else f"{specific_section}.dat"
        all_names = [n for n in all_names if n == clean or n.startswith(specific_section)]

    identical_sections: list[str] = []
    modified_sections: list[dict[str, Any]] = []
    only_in_a: list[str] = []
    only_in_b: list[str] = []

    for full_name in all_names:
        ea = entries_a.get(full_name)
        eb = entries_b.get(full_name)
        if ea is None:
            only_in_b.append(full_name)
            continue
        if eb is None:
            only_in_a.append(full_name)
            continue

        max_sz = max(ea.decompressed_size, eb.decompressed_size)
        if max_sz > deep_diff_max_section_bytes and not specific_section:
            if ea.compressed_size == eb.compressed_size and ea.decompressed_size == eb.decompressed_size:
                identical_sections.append(full_name)
            else:
                modified_sections.append(
                    {
                        "section": full_name,
                        "old_decompressed_size": ea.decompressed_size,
                        "new_decompressed_size": eb.decompressed_size,
                        "size_delta": eb.decompressed_size - ea.decompressed_size,
                        "old_compressed_size": ea.compressed_size,
                        "new_compressed_size": eb.compressed_size,
                        "note": "Section exceeds deep_diff_max_section_bytes; pass specific_section to inspect byte runs.",
                        "diff_runs": [],
                    }
                )
            continue

        raw_a = cont_a.read_raw(ea.name)
        raw_b = cont_b.read_raw(eb.name)
        if raw_a == raw_b:
            identical_sections.append(full_name)
        else:
            runs = _find_byte_diff_runs(raw_a, raw_b, max_runs=max_runs_per_section)
            modified_sections.append(
                {
                    "section": full_name,
                    "old_decompressed_size": len(raw_a),
                    "new_decompressed_size": len(raw_b),
                    "size_delta": len(raw_b) - len(raw_a),
                    "old_sha256": hashlib.sha256(raw_a).hexdigest()[:16],
                    "new_sha256": hashlib.sha256(raw_b).hexdigest()[:16],
                    "diff_runs_count": len(runs),
                    "diff_runs": runs,
                }
            )

    return {
        "save_a": {
            "file": Path(path_a).name,
            "game_date": str(info_a.game_date),
            "build": info_a.build,
        },
        "save_b": {
            "file": Path(path_b).name,
            "game_date": str(info_b.game_date),
            "build": info_b.build,
        },
        "summary": {
            "total_sections_checked": len(all_names),
            "identical_count": len(identical_sections),
            "modified_count": len(modified_sections),
            "only_in_a_count": len(only_in_a),
            "only_in_b_count": len(only_in_b),
        },
        "modified_sections": modified_sections,
        "identical_sections": identical_sections,
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
    }
