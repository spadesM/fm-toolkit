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
        BytePatch(
            key="dof-transfer-targets-sorting",
            title="Futbol Direktörü (DoF) > Transfer Hedefleri ana tablosunda sütun sıralamasını aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle",
            offset=0x1112214,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "26000000526563727569746d656e74446f465472616e73666572546172676574734d61696e426c6f636b000000000000000000000000000000000000050000002200"
            ),
            anchor_delta=0x5BB8,
            original_sha1="68a0857a8ee72920160e7ff3fac0913c5ff3b3e3",
            notes="RecruitmentDoFTransferTargetsMainBlock içindeki 'dof-transfer-targets-table' tablosunda sütun başlığı sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="dof-transfer-targets-global-sorting",
            title="Futbol Direktörü (DoF) > Transfer Hedefleri global tablo bloğunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle",
            offset=0x163782C,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "27000000526563727569746d656e74446f665472616e73666572546172676574735461626c65426c6f636b000000000000000000000000000000000002000000150000"
            ),
            anchor_delta=0x3060,
            original_sha1="f90e1712551338b4edfbaa9ae425e88a4bb8b126",
            notes="RecruitmentDofTransferTargetsTableBlock içindeki StreamedTable üzerinde sıralamayı etkinleştirir.",
        ),
        BytePatch(
            key="set-piece-takers-sorting",
            title="Taktikler > Duran Top Kullanıcıları (StreamedTable_TakersList) tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle",
            offset=0x12B2E40,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "1b000000536574506965636554616b657273426c6f636b54656d706c6174650000000000000000000000000000000000020000001a0000"
            ),
            anchor_delta=0x16B4,
            original_sha1="f90e1712551338b4edfbaa9ae425e88a4bb8b126",
            notes="SetPieceTakersBlockTemplate içindeki 'StreamedTable_TakersList' tablosunda sütun sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="penalty-takers-sorting",
            title="Taktikler > Penaltı Kullanıcıları (SetPiecePenaltyTakersTable) tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle",
            offset=0x12A91B8,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "180000004f6e546865506974636850656e616c74696573426c6f636b00000000000000000000000000000000070000001d000000"
            ),
            anchor_delta=0x887C,
            original_sha1="68a0857a8ee72920160e7ff3fac0913c5ff3b3e3",
            notes="OnThePitchPenaltiesBlock içindeki 'SetPiecePenaltyTakersTable' tablosunda sütun sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="contract-similar-players-sorting",
            title="Sözleşme / Maaş Dağılımı > Benzer Süre Alan Oyuncular tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle",
            offset=0x1522674,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "28000000436f6e7472616374427265616b646f776e46696e616e6369616c427265616b646f776e426c6f636b000000000000000000000000000000000400000019000000"
            ),
            anchor_delta=0x3B38,
            original_sha1="f90e1712551338b4edfbaa9ae425e88a4bb8b126",
            notes="ContractBreakdownFinancialBreakdownBlock içindeki 'TablePlayersWithSimilarPlayingTime' tablosunda sıralamayı açar.",
        ),
        BytePatch(
            key="club-all-staff-sorting",
            title="Kulüp > Tüm Personel / Görev Listesi (StreamedTable_JobsList) tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle",
            offset=0x187D48C,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "11000000436c7562416c6c5374616666426c6f636b000000000000000000000000000000000000000200000017"
            ),
            anchor_delta=0x1420,
            original_sha1="68a0857a8ee72920160e7ff3fac0913c5ff3b3e3",
            notes="ClubAllStaffBlock içindeki 'StreamedTable_JobsList' tablosunda sütun sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="squad-planner-sorting",
            title="Kadro Planlayıcı (RecruitmentSquadPlannerTableBlock) kulüp tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle",
            offset=0x1BBEB00,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "21000000526563727569746d656e745371756164506c616e6e65725461626c65426c6f636b000000000000000000000000000000000000000100000011"
            ),
            anchor_delta=0x5734,
            original_sha1="68a0857a8ee72920160e7ff3fac0913c5ff3b3e3",
            notes="RecruitmentSquadPlannerTableBlock içindeki 'club-table' tablosunda sütun sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="team-reserves-compact-sorting",
            title="Takım > Yedek / Alt Kadro Kompakt tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle",
            offset=0x9FFFD4,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "220000005465616d52657365727665735371756164436f6d706163745461626c65426c6f636b000000000000000000000000000000000000010000001800"
            ),
            anchor_delta=0xAE8,
            original_sha1="68a0857a8ee72920160e7ff3fac0913c5ff3b3e3",
            notes="TeamReservesSquadCompactTableBlock içindeki StreamedTable üzerinde sütun sıralamasını etkinleştirir.",
        ),
        BytePatch(
            key="welcome-pack-best-xi-sorting",
            title="Kulüp Karşılama Paketi > En İyi 11 (WelcomePackBestXIBlock) tablosunda sıralamayı aç (DisableSorting 1 -> 0)",
            bundle="ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle",
            offset=0x174E064,
            original=1,
            patched=0,
            anchor=bytes.fromhex(
                "1600000057656c636f6d655061636b426573745849426c6f636b000000000000000000000000000000000000030000001f00"
            ),
            anchor_delta=0x2A08,
            original_sha1="f90e1712551338b4edfbaa9ae425e88a4bb8b126",
            notes="WelcomePackBestXIBlock içindeki 'PlayersTable' tablosunda sütun sıralamasını etkinleştirir.",
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


def get_all_patches_status(fm_dir: Path) -> list[dict]:
    """Return structured status metadata for all registered patches in ``PATCHES``."""
    stream_cache: dict[str, bytes] = {}
    results: list[dict] = []
    for p in PATCHES.values():
        if isinstance(p, DllImm32Patch):
            path = _dll_path(fm_dir, p)
            bak = path.with_name(path.name + ".bak")
            if not path.exists():
                results.append({
                    "key": p.key,
                    "title": p.title,
                    "kind": "dll_imm32",
                    "target_file": p.dll_name,
                    "state": "MISSING",
                    "is_patched": False,
                    "current_value": None,
                    "default_value": p.default_max_players,
                    "original_value": p.original_max_players,
                    "backup_exists": bak.exists(),
                    "notes": p.notes,
                })
                continue
            try:
                off = _locate_dll_imm32(path, p)
                with path.open("rb") as f:
                    f.seek(off)
                    imm32 = struct.unpack("<I", f.read(4))[0]
                orig_imm32 = (p.original_max_players + 1) * 8
                max_players = (imm32 // 8) - 1 if (imm32 >= 8 and imm32 % 8 == 0) else None
                is_patched = imm32 != orig_imm32 and max_players is not None
                state = "ORIGINAL" if imm32 == orig_imm32 else (f"PATCHED({max_players})" if is_patched else f"UNKNOWN({imm32:#x})")
            except Exception as exc:
                state = f"ERROR({exc})"
                is_patched = False
                max_players = None
            results.append({
                "key": p.key,
                "title": p.title,
                "kind": "dll_imm32",
                "target_file": p.dll_name,
                "state": state,
                "is_patched": is_patched,
                "current_value": max_players,
                "default_value": p.default_max_players,
                "original_value": p.original_max_players,
                "backup_exists": bak.exists(),
                "notes": p.notes,
            })
        else:
            path = _bundle_path(fm_dir, p)
            bak = path.with_name(path.name + ".bak")
            if not path.exists():
                results.append({
                    "key": p.key,
                    "title": p.title,
                    "kind": "bundle_byte",
                    "target_file": p.bundle,
                    "state": "MISSING",
                    "is_patched": False,
                    "current_value": None,
                    "default_value": p.patched,
                    "original_value": p.original,
                    "backup_exists": bak.exists(),
                    "notes": p.notes,
                })
                continue
            try:
                if p.bundle not in stream_cache:
                    stream_cache[p.bundle] = unity_bundle.decompress(path)
                stream = stream_cache[p.bundle]
                off = _locate(stream, p)
                val = int(stream[off])
                is_patched = val == p.patched
                state = "PATCHED" if is_patched else ("ORIGINAL" if val == p.original else f"UNKNOWN({val:#x})")
            except Exception as exc:
                state = f"ERROR({exc})"
                is_patched = False
                val = None
            results.append({
                "key": p.key,
                "title": p.title,
                "kind": "bundle_byte",
                "target_file": p.bundle,
                "state": state,
                "is_patched": is_patched,
                "current_value": val,
                "default_value": p.patched,
                "original_value": p.original,
                "backup_exists": bak.exists(),
                "notes": p.notes,
            })
    return results


def _parse_bundle_reftrees_and_objs(raw: bytes) -> tuple[list[tuple[int, int, int, int, int]], dict[str, list[tuple[int, int, str, str, int, int]]]]:
    """Parse UnityFS SerializedFile ObjectInfo table and RefTypes TypeTree nodes from decompressed stream."""
    data_offset = struct.unpack_from(">Q", raw, 32)[0]
    pos = 48
    end = raw.find(b"\x00", pos)
    pos = end + 1 + 5
    type_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    for _ in range(type_count):
        class_id = struct.unpack_from("<i", raw, pos)[0]
        script_type_index = struct.unpack_from("<h", raw, pos + 5)[0]
        pos += 7
        if class_id == 114 or script_type_index >= 0:
            pos += 16
        pos += 16
        nn, ssz = struct.unpack_from("<II", raw, pos)
        pos += 8 + nn * 32 + ssz
        dep_cnt = struct.unpack_from("<i", raw, pos)[0]
        pos += 4 + dep_cnt * 4

    obj_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    objs: list[tuple[int, int, int, int, int]] = []
    for i in range(obj_count):
        pos = (pos + 3) & ~3
        pid, bstart, bsize, tid = struct.unpack_from("<qQII", raw, pos)
        pos += 24
        objs.append((i, pid, data_offset + bstart, bsize, tid))

    script_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    for _ in range(script_count):
        pos += 4
        pos = (pos + 3) & ~3
        pos += 8

    ext_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    for _ in range(ext_count):
        e = raw.find(b"\x00", pos)
        pos = e + 1 + 16 + 4
        e2 = raw.find(b"\x00", pos)
        pos = e2 + 1

    ref_type_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    ref_trees: dict[str, list[tuple[int, int, str, str, int, int]]] = {}
    for _ in range(ref_type_count):
        class_id = struct.unpack_from("<i", raw, pos)[0]
        script_type_index = struct.unpack_from("<h", raw, pos + 5)[0]
        pos += 7
        if class_id == 114 or script_type_index >= 0:
            pos += 16
        pos += 16
        nn, ssz = struct.unpack_from("<II", raw, pos)
        pos += 8
        nodes_off = pos
        pos += nn * 32
        str_buf = raw[pos : pos + ssz]
        pos += ssz

        def get_rtstr(off: int, sb: bytes = str_buf) -> str:
            if off & 0x80000000:
                return f"common_{off & 0x7FFFFFFF}"
            e = sb.find(b"\x00", off)
            return sb[off:e].decode("ascii", errors="replace")

        nodes: list[tuple[int, int, str, str, int, int]] = []
        for i in range(nn):
            ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from(
                "<HBBIiiiiQ", raw, nodes_off + i * 32
            )
            nodes.append((lvl, tflags, get_rtstr(t_off), get_rtstr(n_off), bsz, mflag))
        e1 = raw.find(b"\x00", pos)
        cls_name = raw[pos:e1].decode("utf-8", errors="replace")
        pos = e1 + 1
        e2 = raw.find(b"\x00", pos)
        pos = e2 + 1
        e3 = raw.find(b"\x00", pos)
        pos = e3 + 1
        ref_trees[cls_name] = nodes
    return objs, ref_trees


def _walk_typetree_node(
    nodes: list[tuple[int, int, str, str, int, int]],
    data: bytes,
    pos: int,
    node_idx: int = 0,
) -> tuple[int, object]:
    lvl, tflags, tname, nname, bsz, mflag = nodes[node_idx]
    children = []
    i = node_idx + 1
    while i < len(nodes) and nodes[i][0] > lvl:
        if nodes[i][0] == lvl + 1:
            children.append(i)
        i += 1
    if tname in ("common_840", "string"):
        slen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        sval = data[pos : pos + slen].decode("utf-8", errors="replace")
        pos += slen
        pos = (pos + 3) & ~3
        return pos, sval
    if tflags & 1:
        cnt = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        elem_node = children[1]
        arr = []
        for _ in range(cnt):
            pos, ev = _walk_typetree_node(nodes, data, pos, elem_node)
            arr.append(ev)
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, arr
    if not children:
        if bsz == 1:
            v: object = data[pos]
        elif bsz == 2:
            v = struct.unpack_from("<H", data, pos)[0]
        elif bsz == 4:
            if tname in ("common_161", "float"):
                v = round(struct.unpack_from("<f", data, pos)[0], 2)
            else:
                v = struct.unpack_from("<i", data, pos)[0]
        elif bsz == 8:
            v = struct.unpack_from("<q", data, pos)[0]
        else:
            v = data[pos : pos + bsz].hex()
        pos += bsz
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, v
    if len(children) == 1 and nodes[children[0]][3] in ("common_49", "Array"):
        pos, arr = _walk_typetree_node(nodes, data, pos, children[0])
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, arr
    obj: dict[str, object] = {}
    for c in children:
        c_name = nodes[c][3]
        pos, cv = _walk_typetree_node(nodes, data, pos, c)
        obj[c_name] = cv
    if mflag & 0x4000:
        pos = (pos + 3) & ~3
    return pos, obj


def scan_all_streamed_tables(fm_dir: Path, only_unsortable_by_default: bool = True) -> list[dict]:
    """Scan all UI VisualTreeAsset preload bundles and list ``StreamedTable`` instances and their ``DisableSorting`` byte."""
    aa = fm_dir / AA_DIR
    if not aa.exists():
        return []
    items: list[dict] = []
    for bp in sorted(aa.glob("ui-visualtreeassets*.bundle")):
        bname = bp.name
        try:
            cur_stream = unity_bundle.decompress(bp)
            bak_path = bp.with_name(bp.name + ".bak")
            orig_stream = unity_bundle.decompress(bak_path) if bak_path.exists() else cur_stream
            objs, ref_trees = _parse_bundle_reftrees_and_objs(orig_stream)
        except Exception:
            continue
        if "StreamedTable/UxmlSerializedData" not in ref_trees:
            continue
        st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
        top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

        for _oi, (_idx, pid, abs_off, bsize, _tid) in enumerate(objs):
            chunk = orig_stream[abs_off : abs_off + bsize]
            if b"StreamedTable/UxmlSerializedData" not in chunk:
                continue
            ln = struct.unpack_from("<I", chunk, 28)[0] if len(chunk) >= 32 else 0
            vta_name = chunk[32 : 32 + ln].decode("utf-8", "replace") if 0 < ln < 200 else "UnknownVTA"
            pos = 0
            while True:
                idx = chunk.find(b"StreamedTable/UxmlSerializedData", pos)
                if idx < 0:
                    break
                pos = idx + 1
                p = idx + 64
                fields: dict[str, object] = {}
                offsets: dict[str, int] = {}
                for c in top_children:
                    cname = st_nodes[c][3]
                    if cname == "references":
                        break
                    start = p
                    try:
                        p, val = _walk_typetree_node(st_nodes, chunk, p, c)
                    except Exception:
                        break
                    if not cname.endswith("_UxmlAttributeFlags"):
                        fields[cname] = val
                        offsets[cname] = abs_off + start
                ds_off = offsets.get("DisableSorting")
                if ds_off is None or ds_off >= len(cur_stream):
                    continue
                orig_ds = int(orig_stream[ds_off])
                cur_ds = int(cur_stream[ds_off])
                if only_unsortable_by_default and orig_ds != 1 and cur_ds != 1:
                    continue
                binding_obj = fields.get("Binding")
                binding_str = binding_obj.get("m_path", "") if isinstance(binding_obj, dict) else str(binding_obj or "")
                items.append({
                    "bundle": bname,
                    "vta_name": vta_name,
                    "path_id": pid,
                    "table_name": str(fields.get("name") or ""),
                    "binding": str(binding_str or ""),
                    "offset": ds_off,
                    "offset_hex": f"{ds_off:#x}",
                    "disable_sorting": cur_ds,
                    "original_disable_sorting": orig_ds,
                    "sorting_enabled": cur_ds == 0,
                    "is_modified": cur_ds != orig_ds,
                })
    return items


def set_streamed_table_sorting(fm_dir: Path, bundle_name: str, offset: int, disable_sorting: int) -> dict:
    """Set ``DisableSorting`` (`0` = sortable, `1` = disabled) at ``offset`` in ``bundle_name``."""
    if disable_sorting not in (0, 1):
        raise ValueError("disable_sorting must be 0 or 1")
    path = fm_dir / AA_DIR / bundle_name
    if not path.exists():
        raise FileNotFoundError(f"Bundle not found: {path}")
    bundle = unity_bundle.read_bundle(path)
    stream = unity_bundle.decompress(bundle)
    if not (0 <= offset < len(stream)):
        raise ValueError(f"Offset {offset:#x} out of range for {bundle_name}")
    # Verify that StreamedTable/UxmlSerializedData header precedes offset within 0x500 bytes
    window_start = max(0, offset - 0x500)
    if b"StreamedTable/UxmlSerializedData" not in stream[window_start:offset]:
        raise RuntimeError(f"Offset {offset:#x} is not inside a StreamedTable/UxmlSerializedData block")
    cur_val = int(stream[offset])
    if cur_val == disable_sorting:
        return {"ok": True, "changed": False, "bundle": bundle_name, "offset": offset, "disable_sorting": cur_val}
    new_bytes = unity_bundle.patch_bytes(bundle, {offset: bytes([disable_sorting])})
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    tmp = path.with_name(path.name + ".patched.tmp")
    tmp.write_bytes(new_bytes)
    try:
        verify_stream = unity_bundle.decompress(tmp)
        if int(verify_stream[offset]) != disable_sorting:
            raise RuntimeError("Verification failed after patching StreamedTable")
        shutil.move(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()
    return {"ok": True, "changed": True, "bundle": bundle_name, "offset": offset, "disable_sorting": disable_sorting}



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
