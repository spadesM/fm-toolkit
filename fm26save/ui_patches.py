"""Football Manager 27 UI & Native Engine Patches (Unity Addressables bundles & game_plugin.dll).

Supports two kinds of surgical patches:
1. :class:`BytePatch` — flips a serialized UXML attribute byte inside a UI ``.bundle``
   file using :mod:`fm26save.unity_bundle` (only the affected LZ4 block is re-compressed
   and verified byte-for-byte).
2. :class:`DllImm32Patch` — modifies a 32-bit immediate constant inside ``game_plugin.dll``
   (verified via an 11-byte x86-64 instruction prefix + 2-byte jump opcode suffix).

Available patches
-----------------
``scout-priorities-sorting``
    Scouting -> Scout Priorities player list (``ScoutPrioritiesBlock``) ships with
    ``StreamedTable.DisableSorting = 1``, so no column header gets a click handler.
    The patch sets it to ``0`` (the Player Database table already uses ``0``).
    Full analysis: ``docs/FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md``.

``scout-player-limit``
    Player Database / Scouting multi-select context menu enforces a hardcoded maximum of
    **50 players** in ``EvaluateScoutPlayersAction`` (``VA = 0x180FDE520``, check at
    ``VA = 0x180FDEBD4``, raw offset ``0x00FDDFD4``: ``cmp rcx, 0x198`` where
    ``0x198 = (50 + 1) * 8`` bytes in ``std::vector<Person*>``). When 51+ players are
    selected, it sets FourCC ``'tmpa'`` (*Too Many Players Action*) and disables scouting.
    The patch raises this limit to ``--max-players`` (default: ``5000``).
    Full analysis: ``docs/FM27_SCOUTING_50_PLAYER_LIMIT_FIX_TR.md``.

Usage
-----
::

    python -m fm26save.ui_patches list
    python -m fm26save.ui_patches status  scout-priorities-sorting
    python -m fm26save.ui_patches apply   scout-priorities-sorting [--dry-run]
    python -m fm26save.ui_patches restore scout-priorities-sorting

    python -m fm26save.ui_patches status  scout-player-limit
    python -m fm26save.ui_patches apply   scout-player-limit [--max-players 5000] [--dry-run]
    python -m fm26save.ui_patches restore scout-player-limit
    # optional: --fm-dir "C:\\...\\Football Manager 27"

Close the game before applying/restoring. A one-time ``<target>.bak`` copy of the
original file is created before the first write; ``restore`` copies it back.
Steam "Verify integrity of game files" or a game update also restores the original.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from fm26save import unity_bundle

DEFAULT_FM27_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27")
AA_DIR = Path("fm_Data/StreamingAssets/aa/StandaloneWindows64")
PLUGIN_DIR = Path("fm_Data/Plugins/x86_64")


@dataclass(frozen=True)
class BytePatch:
    key: str
    title: str
    bundle: str  #: file name inside fm_Data/StreamingAssets/aa/StandaloneWindows64
    offset: int  #: expected uncompressed offset of the byte (FM27 build of 2.11.2026)
    original: int
    patched: int
    anchor: bytes  #: unique serialized bytes near the target, used to re-locate after updates
    anchor_delta: int  #: offset - anchor position
    original_sha1: str  #: SHA1 of the untouched bundle the offsets were taken from
    notes: str = ""


@dataclass(frozen=True)
class DllImm32Patch:
    key: str
    title: str
    dll_name: str  #: file name inside fm_Data/Plugins/x86_64
    offset: int  #: raw file offset of the uint32_le immediate
    va: int  #: virtual address of the uint32_le immediate (image_base = 0x180000000)
    original_max_players: int  #: 50 -> imm32 = (50 + 1) * 8 = 0x198
    default_max_players: int  #: default replacement max_players (e.g. 5000 -> imm32 = 0x9C48)
    anchor: bytes  #: instruction bytes immediately preceding the imm32
    anchor_delta: int  #: offset - anchor position
    suffix: bytes  #: instruction bytes immediately following the imm32
    notes: str = ""


AnyPatch = Union[BytePatch, DllImm32Patch]

PATCHES: dict[str, AnyPatch] = {
    p.key: p
    for p in [
        BytePatch(
            key="scout-priorities-sorting",
            title="Gözlemcilik > Gözlemci Öncelikleri listesinde sütun sıralamasını aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle",
            offset=0x1194584,
            original=1,
            patched=0,
            # MovedItemBinding path string that directly precedes DisableSorting in
            # ScoutPrioritiesBlock's StreamedTable/UxmlSerializedData
            anchor=b"Team.ScoutPriorities.SpecificallyScoutedPlayerMove",
            anchor_delta=0x1194584 - 0x119454C,
            original_sha1="f90e1712551338b4edfbaa9ae425e88a4bb8b126",
            notes=(
                "Liste sıralıyken sürükle-bırak ile öncelik değiştirmeyin (satır sırası = öncelik). "
                "Atanan gözlemci / kalan ilerleme / görev süresi sütunlarının sıralama yolu yoktur."
            ),
        ),
        DllImm32Patch(
            key="scout-player-limit",
            title="Oyuncu Merkezi / Gözlemcilik çoklu seçimde 50 oyuncu gözlemleme sınırını yükselt (cmp rcx, (N+1)*8)",
            dll_name="game_plugin.dll",
            offset=0x00FDDFD7,
            va=0x180FDEBD7,
            original_max_players=50,
            default_max_players=5000,
            # 0x180fdebcc: 48 8b 4d e8          mov rcx, qword ptr [rbp - 0x18]
            # 0x180fdebd0: 48 2b 4d e0          sub rcx, qword ptr [rbp - 0x20]
            # 0x180fdebd4: 48 81 f9 <imm32>     cmp rcx, (max_players + 1) * 8
            # 0x180fdebdb: 0f 83 e7 0b 00 00    jae 0x180fdf7c8
            anchor=bytes.fromhex("488b4de8482b4de04881f9"),
            anchor_delta=11,
            suffix=bytes.fromhex("0f83"),
            notes=(
                "Varsayılan olarak tek seferde 5000 oyuncuya kadar gözlemleme (Rapor İste / Gözlemle) açılır. "
                "Özel bir sınır için --max-players <SAYI> parametresini kullanabilirsiniz."
            ),
        ),
    ]
}

PATCH_ALIASES: dict[str, str] = {
    "scouting-priorities-sorting": "scout-priorities-sorting",
    "scouting-player-limit": "scout-player-limit",
}


def resolve_patch(name: str | None) -> AnyPatch | None:
    if not name:
        return None
    canonical = PATCH_ALIASES.get(name, name)
    return PATCHES.get(canonical)


def _bundle_path(fm_dir: Path, patch: BytePatch) -> Path:
    return fm_dir / AA_DIR / patch.bundle


def _dll_path(fm_dir: Path, patch: DllImm32Patch) -> Path:
    return fm_dir / PLUGIN_DIR / patch.dll_name


def _locate(stream: bytes, patch: BytePatch) -> int:
    """Return the uncompressed offset of the target byte (validated via the anchor)."""
    a = patch.offset - patch.anchor_delta
    if stream[a : a + len(patch.anchor)] == patch.anchor:
        return patch.offset
    hits = []
    start = 0
    while (i := stream.find(patch.anchor, start)) >= 0:
        hits.append(i)
        start = i + 1
    if len(hits) != 1:
        raise RuntimeError(f"anchor {patch.anchor!r} found {len(hits)} times - unknown game version, aborting")
    return hits[0] + patch.anchor_delta


def _locate_dll_imm32(path: Path, patch: DllImm32Patch) -> int:
    """Return the raw file offset of the 4-byte immediate inside game_plugin.dll."""
    a = patch.offset - patch.anchor_delta
    window_len = len(patch.anchor) + 4 + len(patch.suffix)
    with path.open("rb") as f:
        f.seek(a)
        window = f.read(window_len)
    if (
        len(window) == window_len
        and window[: len(patch.anchor)] == patch.anchor
        and window[len(patch.anchor) + 4 :] == patch.suffix
    ):
        return patch.offset

    data = path.read_bytes()
    hits = []
    start = 0
    while (i := data.find(patch.anchor, start)) >= 0:
        suf_start = i + len(patch.anchor) + 4
        if data[suf_start : suf_start + len(patch.suffix)] == patch.suffix:
            hits.append(i)
        start = i + 1
    if len(hits) != 1:
        raise RuntimeError(
            f"anchor {patch.anchor.hex()} + imm32 + {patch.suffix.hex()} found {len(hits)} times "
            f"in {path.name} - unknown game version, aborting"
        )
    return hits[0] + patch.anchor_delta


def _status_dll(fm_dir: Path, patch: DllImm32Patch) -> str:
    path = _dll_path(fm_dir, patch)
    off = _locate_dll_imm32(path, patch)
    with path.open("rb") as f:
        f.seek(off)
        imm32 = struct.unpack("<I", f.read(4))[0]
    orig_imm32 = (patch.original_max_players + 1) * 8
    max_players = (imm32 // 8) - 1 if (imm32 >= 8 and imm32 % 8 == 0) else None
    if imm32 == orig_imm32:
        state = "ORIGINAL"
    elif max_players is not None:
        state = f"PATCHED(max_players={max_players})"
    else:
        state = f"UNKNOWN({imm32:#x})"
    bak = path.with_name(path.name + ".bak")
    print(
        f"[{patch.key}] {path.name}: imm32 @ {off:#x} (VA {patch.va:#x}) = {imm32:#x} "
        f"(max_players={max_players}) -> {state}; backup: {'yes' if bak.exists() else 'no'}"
    )
    return state


def status(fm_dir: Path, patch: AnyPatch) -> str:
    if isinstance(patch, DllImm32Patch):
        return _status_dll(fm_dir, patch)
    path = _bundle_path(fm_dir, patch)
    stream = unity_bundle.decompress(path)
    off = _locate(stream, patch)
    value = stream[off]
    state = {patch.original: "ORIGINAL", patch.patched: "PATCHED"}.get(value, f"UNKNOWN({value:#x})")
    bak = path.with_name(path.name + ".bak")
    print(f"[{patch.key}] {path.name}: byte @ {off:#x} = {value:#x} -> {state}; backup: {'yes' if bak.exists() else 'no'}")
    return state


def _apply_dll(
    fm_dir: Path,
    patch: DllImm32Patch,
    dry_run: bool = False,
    max_players: int | None = None,
) -> int:
    target_max = patch.default_max_players if max_players is None else max_players
    if not (1 <= target_max <= 100_000):
        print(f"[{patch.key}] invalid --max-players {target_max} (must be between 1 and 100000)")
        return 2
    target_imm32 = (target_max + 1) * 8
    target_bytes = struct.pack("<I", target_imm32)

    path = _dll_path(fm_dir, patch)
    off = _locate_dll_imm32(path, patch)
    with path.open("rb") as f:
        f.seek(off)
        cur_imm32 = struct.unpack("<I", f.read(4))[0]
    cur_max = (cur_imm32 // 8) - 1 if (cur_imm32 >= 8 and cur_imm32 % 8 == 0) else None

    if cur_imm32 == target_imm32:
        print(f"[{patch.key}] already patched to max_players={target_max} (imm32={target_imm32:#x})")
        return 0
    if cur_max is None:
        print(f"[{patch.key}] unexpected imm32 {cur_imm32:#x} @ {off:#x} - aborting")
        return 2

    print(
        f"[{patch.key}] verified instruction anchor @ {off - patch.anchor_delta:#x}; "
        f"imm32 @ {off:#x} (VA {patch.va:#x}): {cur_imm32:#x} (max_players={cur_max}) -> "
        f"{target_imm32:#x} (max_players={target_max})"
    )
    if dry_run:
        print(f"[{patch.key}] dry run - nothing written")
        return 0

    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"[{patch.key}] backup created: {bak}")

    with path.open("r+b") as f:
        f.seek(off)
        f.write(target_bytes)
        f.flush()

    # Re-verify anchor, immediate, and suffix in place
    verify_off = _locate_dll_imm32(path, patch)
    with path.open("rb") as f:
        f.seek(verify_off)
        new_imm32 = struct.unpack("<I", f.read(4))[0]
    if new_imm32 != target_imm32:
        raise RuntimeError(f"verification failed: expected {target_imm32:#x}, got {new_imm32:#x}")

    print(f"[{patch.key}] patched: {path} (max_players={target_max})")
    if patch.notes:
        print(f"[{patch.key}] NOT: {patch.notes}")
    return 0


def apply(
    fm_dir: Path,
    patch: AnyPatch,
    dry_run: bool = False,
    max_players: int | None = None,
) -> int:
    if isinstance(patch, DllImm32Patch):
        return _apply_dll(fm_dir, patch, dry_run=dry_run, max_players=max_players)

    path = _bundle_path(fm_dir, patch)
    bundle = unity_bundle.read_bundle(path)
    stream = unity_bundle.decompress(bundle)
    off = _locate(stream, patch)
    if stream[off] == patch.patched:
        print(f"[{patch.key}] already patched")
        return 0
    if stream[off] != patch.original:
        print(f"[{patch.key}] unexpected byte {stream[off]:#x} @ {off:#x} - aborting")
        return 2
    sha1 = hashlib.sha1(bundle.data).hexdigest()
    if sha1 != patch.original_sha1:
        print(f"[{patch.key}] note: bundle SHA1 {sha1} differs from the analysed build (anchor still matched)")

    new = unity_bundle.patch_bytes(bundle, {off: bytes([patch.patched])})
    tmp = path.with_name(path.name + ".patched.tmp")
    tmp.write_bytes(new)
    try:
        new_stream = unity_bundle.decompress(tmp)
        if len(new_stream) != len(stream):
            raise RuntimeError("decompressed length changed")
        diffs = [i for i in range(len(stream)) if stream[i] != new_stream[i]]
        if diffs != [off]:
            raise RuntimeError(f"verification failed, differing offsets: {[hex(d) for d in diffs[:10]]}")
        print(f"[{patch.key}] verified: only byte {off:#x} changed ({patch.original} -> {patch.patched}); "
              f"file size {len(bundle.data)} -> {len(new)}")
        if dry_run:
            print(f"[{patch.key}] dry run - nothing written")
            return 0
        bak = path.with_name(path.name + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
            print(f"[{patch.key}] backup created: {bak}")
        shutil.move(str(tmp), str(path))
        print(f"[{patch.key}] patched: {path}")
        if patch.notes:
            print(f"[{patch.key}] NOT: {patch.notes}")
        return 0
    finally:
        if tmp.exists():
            tmp.unlink()


def restore(fm_dir: Path, patch: AnyPatch) -> int:
    path = _dll_path(fm_dir, patch) if isinstance(patch, DllImm32Patch) else _bundle_path(fm_dir, patch)
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        print(f"[{patch.key}] no backup at {bak}")
        return 1
    shutil.copy2(bak, path)
    print(f"[{patch.key}] restored {path.name} from backup")
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="python -m fm26save.ui_patches", description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["list", "status", "apply", "restore"])
    ap.add_argument("patch", nargs="?", help="patch key (see 'list')")
    ap.add_argument("--fm-dir", type=Path, default=DEFAULT_FM27_DIR, help="Football Manager 27 install directory")
    ap.add_argument("--dry-run", action="store_true", help="verify only, do not write")
    ap.add_argument(
        "--max-players",
        type=int,
        default=None,
        help="Replacement player limit for 'scout-player-limit' (default: 5000)",
    )
    args = ap.parse_args(argv)

    if args.command == "list":
        for p in PATCHES.values():
            target_desc = f"dll: {p.dll_name}" if isinstance(p, DllImm32Patch) else f"bundle: {p.bundle}"
            print(f"{p.key:28s} {p.title}\n{'':28s} {target_desc}")
        return 0
    patch = resolve_patch(args.patch)
    if patch is None:
        ap.error(f"unknown patch {args.patch!r}; choose from {', '.join(PATCHES)}")
    if args.command == "status":
        status(args.fm_dir, patch)
        return 0
    if args.command == "apply":
        return apply(args.fm_dir, patch, dry_run=args.dry_run, max_players=args.max_players)
    return restore(args.fm_dir, patch)


if __name__ == "__main__":
    sys.exit(main())
