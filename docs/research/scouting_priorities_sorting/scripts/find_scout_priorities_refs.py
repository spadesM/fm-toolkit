import os, sys, glob, struct
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

# Dump all UxmlSerializedData inside Obj 177, Obj 229, Obj 263, Obj 360
for oi in (177, 229, 263, 360):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    print(f"\n================ Obj {oi} ({name}) ================")
    # Find all /UxmlSerializedData in chunk
    pos = 0
    while True:
        idx = chunk.find(b"/UxmlSerializedData", pos)
        if idx == -1:
            break
        # Walk backwards to find start of class name
        s_start = idx
        while s_start > 0 and 32 <= chunk[s_start - 1] < 127:
            s_start -= 1
        cls_len = struct.unpack_from("<I", chunk, s_start - 4)[0]
        cls_name = chunk[s_start : s_start + cls_len].decode("utf-8", errors="replace")
        # After cls_name (aligned to 4), namespace (aligned to 4), assembly (aligned to 4)
        p = s_start - 4 + 4 + ((cls_len + 3) & ~3)
        ns_len = struct.unpack_from("<I", chunk, p)[0]
        ns_name = chunk[p+4 : p+4+ns_len].decode("utf-8", errors="replace")
        p += 4 + ((ns_len + 3) & ~3)
        asm_len = struct.unpack_from("<I", chunk, p)[0]
        asm_name = chunk[p+4 : p+4+asm_len].decode("utf-8", errors="replace")
        data_off = p + 4 + ((asm_len + 3) & ~3)
        print(f"  [+{s_start-4:#x}] {ns_name}.{cls_name} ({asm_name}) data_off={data_off:#x}")
        if cls_name in ref_trees:
            rnodes = ref_trees[cls_name]
            top_c = [i for i, n in enumerate(rnodes) if n[0] == 1]
            dp = data_off
            for c in top_c[:-1]:
                cname = rnodes[c][3]
                try:
                    dp_next, val = walk_tree(rnodes, chunk, dp, c)
                except Exception as e:
                    print(f"    ERR at {cname}: {e}")
                    break
                if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2, -1, -1.0) and not cname.endswith("_UxmlAttributeFlags"):
                    print(f"    {cname}: {val}")
                dp = dp_next
        pos = idx + 19
