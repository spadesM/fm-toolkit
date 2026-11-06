"""Football Manager 27 UI patches (Unity Addressables bundle edits).

Each patch flips a serialized UXML attribute inside a UI ``.bundle`` file of the
game installation. Patches are applied surgically with :mod:`fm26save.unity_bundle`:
only the storage block that contains the byte is re-compressed and the result is
verified to differ from the original **only** at the patched byte(s).

Available patches
-----------------
``scout-priorities-sorting``
    Scouting -> Scout Priorities player list (``ScoutPrioritiesBlock``) ships with
    ``StreamedTable.DisableSorting = 1``, so no column header gets a click handler.
    The patch sets it to ``0`` (the Player Database table already uses ``0``).
    Full analysis: ``docs/FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md``.

Usage
-----
::

    python -m fm26save.ui_patches list
    python -m fm26save.ui_patches status  scout-priorities-sorting
    python -m fm26save.ui_patches apply   scout-priorities-sorting [--dry-run]
    python -m fm26save.ui_patches restore scout-priorities-sorting
    # optional: --fm-dir "C:\\...\\Football Manager 27"

Close the game before applying/restoring. A one-time ``<bundle>.bak`` copy of the
original file is created before the first write; ``restore`` copies it back.
Steam "Verify integrity of game files" or a game update also restores the original.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from fm26save import unity_bundle

DEFAULT_FM27_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27")
AA_DIR = Path("fm_Data/StreamingAssets/aa/StandaloneWindows64")


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


PATCHES: dict[str, BytePatch] = {
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
    ]
}


def _bundle_path(fm_dir: Path, patch: BytePatch) -> Path:
    return fm_dir / AA_DIR / patch.bundle


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


def status(fm_dir: Path, patch: BytePatch) -> str:
    path = _bundle_path(fm_dir, patch)
    stream = unity_bundle.decompress(path)
    off = _locate(stream, patch)
    value = stream[off]
    state = {patch.original: "ORIGINAL", patch.patched: "PATCHED"}.get(value, f"UNKNOWN({value:#x})")
    bak = path.with_name(path.name + ".bak")
    print(f"[{patch.key}] {path.name}: byte @ {off:#x} = {value:#x} -> {state}; backup: {'yes' if bak.exists() else 'no'}")
    return state


def apply(fm_dir: Path, patch: BytePatch, dry_run: bool = False) -> int:
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


def restore(fm_dir: Path, patch: BytePatch) -> int:
    path = _bundle_path(fm_dir, patch)
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        print(f"[{patch.key}] no backup at {bak}")
        return 1
    shutil.copy2(bak, path)
    print(f"[{patch.key}] restored {path.name} from backup")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fm26save.ui_patches", description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["list", "status", "apply", "restore"])
    ap.add_argument("patch", nargs="?", help="patch key (see 'list')")
    ap.add_argument("--fm-dir", type=Path, default=DEFAULT_FM27_DIR, help="Football Manager 27 install directory")
    ap.add_argument("--dry-run", action="store_true", help="verify only, do not write")
    args = ap.parse_args(argv)

    if args.command == "list":
        for p in PATCHES.values():
            print(f"{p.key:28s} {p.title}\n{'':28s} bundle: {p.bundle}")
        return 0
    if args.patch not in PATCHES:
        ap.error(f"unknown patch {args.patch!r}; choose from {', '.join(PATCHES)}")
    patch = PATCHES[args.patch]
    if args.command == "status":
        status(args.fm_dir, patch)
        return 0
    if args.command == "apply":
        return apply(args.fm_dir, patch, args.dry_run)
    return restore(args.fm_dir, patch)


if __name__ == "__main__":
    sys.exit(main())
