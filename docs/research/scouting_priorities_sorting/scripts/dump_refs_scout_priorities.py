import sys, struct, re
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

for oi in (229, 263, 360):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    print(f"\n================ Obj {oi}: {name} (size={bsize}) ================")
    for m in re.finditer(rb"[A-Za-z0-9_]+/UxmlSerializedData", chunk):
        cls = m.group(0).decode("ascii")
        p = (m.end() + 3) & ~3
        l2 = struct.unpack_from("<I", chunk, p)[0]; p += 4 + ((l2 + 3) & ~3)
        l3 = struct.unpack_from("<I", chunk, p)[0]; p += 4 + ((l3 + 3) & ~3)
        rnodes = ref_trees.get(cls)
        if rnodes:
            try:
                end_p, rval = walk_tree(rnodes, chunk, p, 0)
                clean = {k: v for k, v in rval.items() if not k.endswith("_UxmlAttributeFlags") and v not in (0, "", [], None, {"m_FileID": 0, "m_PathID": 0}, {"m_path": ""})}
                print(f"  @{m.start()} {cls}: {clean}")
            except Exception as e:
                print(f"  @{m.start()} {cls}: ERROR {e}")
        else:
            print(f"  @{m.start()} {cls}: NO_REF_TREE")
