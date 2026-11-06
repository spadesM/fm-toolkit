import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    if any(k in chunk for k in (b"ScoutPriorit", b"SpecificallyScouted", b"399c0aa9357f67847b91ba2fe4756083", b"13a1f18bd93e860488c2cb84abb1168c")):
        ln = struct.unpack_from("<I", chunk, 28)[0] if len(chunk) >= 32 else 0
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else f"obj_{oi}"
        print(f"\n==================== Obj {oi} ({name}, size={bsize}, pid={pid}) ====================")
        pat = b"StreamedTable/UxmlSerializedData"
        pos = 0
        while True:
            idx = chunk.find(pat, pos)
            if idx == -1: break
            pos = idx + 1
            p = idx + 64
            print(f"  --- StreamedTable at +{idx} (dstart={p}) ---")
            for c in top_children:
                cname = st_nodes[c][3]
                try:
                    p_next, val = walk_tree(st_nodes, chunk, p, c)
                    if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                        print(f"    +0x{p - (idx+64):03x} {cname}: {val}")
                    p = p_next
                except Exception as e:
                    print(f"    ERROR at {cname}: {e}")
                    break
        # Also print all readable strings in Obj 177 if no StreamedTable
        if oi in (177, 85):
            import re
            strs = [m.group(0).decode("ascii") for m in re.finditer(rb"[ -~]{4,}", chunk)]
            print(f"  Strings: {strs}")
