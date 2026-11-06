import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

for target_oi in (229, 263):
    _, pid, abs_off, bsize, tid = objs[target_oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    print(f"\n==================== Obj {target_oi}: {name} (pid={pid}) ====================")
    pos = 0
    while True:
        idx = chunk.find(b"/UxmlSerializedData", pos)
        if idx == -1:
            break
        cname = None
        cstart = None
        for back in range(4, 80):
            if (idx - back) % 4 != 0:
                continue
            cand_len = struct.unpack_from("<I", chunk, idx - back)[0]
            if cand_len == back + len("/UxmlSerializedData") - 4:
                cname = chunk[idx - back + 4 : idx + len("/UxmlSerializedData")].decode("ascii", errors="replace")
                cstart = idx - back
                break
        if cname and cname in ref_trees and "VisualElement/UxmlSerializedData" not in cname:
            p = cstart + 4 + ((len(cname) + 3) & ~3)
            ns_len = struct.unpack_from("<I", chunk, p)[0]
            p += 4 + ((ns_len + 3) & ~3)
            asm_len = struct.unpack_from("<I", chunk, p)[0]
            p += 4 + ((asm_len + 3) & ~3)
            rnodes = ref_trees[cname]
            top_c = [i for i, n in enumerate(rnodes) if n[0] == 1]
            print(f"  [{cname} @ {p}]")
            for c in top_c:
                fn = rnodes[c][3]
                if fn == "references":
                    break
                try:
                    p, val = walk_tree(rnodes, chunk, p, c)
                    if not fn.endswith("_UxmlAttributeFlags") and val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                        print(f"    {fn}: {val}")
                except Exception as e:
                    print(f"    err at {fn}: {e}")
                    break
        pos = idx + 19
