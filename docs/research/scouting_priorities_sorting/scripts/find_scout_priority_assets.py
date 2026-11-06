import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

for i, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 36:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        if 0 < ln < 200:
            name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
            if any(k in name.lower() for k in ("priorit", "specific", "scout")) or b"99226" in chunk or b"ScoutPriorit" in chunk:
                print(f"Obj {i:3d} (PathID={pid}, size={bsize}): {name}")
