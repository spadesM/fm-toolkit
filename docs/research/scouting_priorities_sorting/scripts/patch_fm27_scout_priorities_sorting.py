"""Patch FM27 ScoutPrioritiesBlock: StreamedTable.DisableSorting 1 -> 0 (Gözlemcilik Öncelikleri listesinde sıralamayı açar).

- Bundle : fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle
- Object : ScoutPrioritiesBlock (VisualTreeAsset, PathID 2056832882284531458)
- Field  : StreamedTable/UxmlSerializedData.DisableSorting @ uncompressed offset 0x1194584

Usage:
  python patch_fm27_scout_priorities_sorting.py            -> dry run (verify only, writes nothing)
  python patch_fm27_scout_priorities_sorting.py --apply    -> create .bak (once) and write patched bundle
  python patch_fm27_scout_priorities_sorting.py --restore  -> restore from .bak
"""
import sys, struct, shutil, hashlib
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
import lz4.block
from fm26save.binary_decompiler import unpack_unityfs_bundle, lz4_decompress_block
from bundle_locate_byte import parse_bundle

BUNDLE = use_fm27.FM27 / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle"
BAK = BUNDLE.with_name(BUNDLE.name + ".bak")
TARGET = 0x1194584
# Serialized context right before the flag: ...MovedItemBinding path "Team.ScoutPriorities.SpecificallyScoutedPlayerMove"
CONTEXT = b"SpecificallyScoutedPlayerMove"


def rebuild(data, info, new_blocks_c, new_blocks_flags):
    """Rebuild a UnityFS v8 bundle with replaced compressed blocks."""
    bi = bytearray(info["bi"])
    b = 20
    for i, blk in enumerate(info["blocks"]):
        struct.pack_into(">IIH", bi, b, blk["u_sz"], len(new_blocks_c[i]), new_blocks_flags[i])
        b += 10
    c_type = info["flags"] & 0x3F
    if c_type in (2, 3):
        bi_c = lz4.block.compress(bytes(bi), mode="high_compression", compression=12, store_size=False)
    else:
        bi_c = bytes(bi)
    head = bytearray(data[: info["hdr_pos"]])
    body = bytearray()
    hdr_len = info["hdr_pos"] + 20
    pre = bytearray()
    pre += head
    pre += b"\x00" * 20  # placeholder
    if info["ver"] >= 7:
        while len(pre) % 16: pre += b"\x00"
    pre += bi_c
    if info["flags"] & 0x200:
        while len(pre) % 16: pre += b"\x00"
    for c in new_blocks_c:
        body += c
    total = len(pre) + len(body)
    struct.pack_into(">QIII", pre, info["hdr_pos"], total, len(bi_c), len(bi), info["flags"])
    return bytes(pre + body)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry"
    if mode == "--restore":
        if not BAK.exists():
            print("No backup found:", BAK); return 1
        shutil.copy2(BAK, BUNDLE)
        print("Restored", BUNDLE, "from", BAK); return 0

    src_path = BAK if BAK.exists() else BUNDLE  # always patch from pristine original
    data = src_path.read_bytes()
    info = parse_bundle(data)
    raw = unpack_unityfs_bundle(src_path)
    ctx_at = raw.find(CONTEXT, TARGET - 0x40, TARGET)
    print(f"source={src_path.name} size={len(data)} sha1={hashlib.sha1(data).hexdigest()}")
    print(f"context '{CONTEXT.decode()}' at {ctx_at:#x}; DisableSorting byte = {raw[TARGET]:#x}")
    if ctx_at < 0 or raw[TARGET] != 1:
        print("Unexpected content - aborting (game version changed?)"); return 2

    # sanity: rebuild without changes must decompress to identical content
    blocks_c = [data[b["c_off"]: b["c_off"] + b["c_sz"]] for b in info["blocks"]]
    flags = [b["flags"] for b in info["blocks"]]

    # patch target block
    for i, blk in enumerate(info["blocks"]):
        if blk["u_off"] <= TARGET < blk["u_off"] + blk["u_sz"]:
            dec = bytearray(lz4_decompress_block(blocks_c[i], blk["u_sz"]) if blk["flags"] & 0x3F in (2, 3) else blocks_c[i])
            dec[TARGET - blk["u_off"]] = 0
            if blk["flags"] & 0x3F in (2, 3):
                blocks_c[i] = lz4.block.compress(bytes(dec), mode="high_compression", compression=12, store_size=False)
            else:
                blocks_c[i] = bytes(dec)
            print(f"block {i}: c_sz {blk['c_sz']} -> {len(blocks_c[i])}")
            break
    new = rebuild(data, info, blocks_c, flags)

    tmp = BUNDLE.with_name(BUNDLE.name + ".patched.tmp")
    tmp.write_bytes(new)
    new_raw = unpack_unityfs_bundle(tmp)
    diffs = [i for i in range(len(raw)) if raw[i] != new_raw[i]] if len(raw) == len(new_raw) else None
    print(f"new size={len(new)} uncompressed equal-length={len(raw) == len(new_raw)} diffs={[hex(d) for d in diffs] if diffs is not None else 'LEN MISMATCH'}")
    ok = diffs == [TARGET]
    if not ok:
        tmp.unlink(); print("Verification FAILED - nothing written"); return 3
    if mode != "--apply":
        tmp.unlink(); print("Dry run OK (use --apply to write)"); return 0
    if not BAK.exists():
        shutil.copy2(BUNDLE, BAK); print("Backup created:", BAK)
    shutil.move(str(tmp), str(BUNDLE))
    print("Patched:", BUNDLE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
