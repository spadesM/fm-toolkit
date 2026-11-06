import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

print("=== 1. Dump ApplyStateChanges (0x015aab80..0x015ab300) and end of QueueStateEvent (0x00abdee0..0x00abe050) ===")
dhf.dump_fast("ApplyStateChanges_0x015aab80", 0x015aab80, 0x015ab300)
dhf.dump_fast("QueueStateEvent_end", 0x00abdee0, 0x00abe050)

print("\n=== 2. Inspect StreamedTable in all ui-recruitment_assets_all.bundle objects ===")
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees.get("StreamedTable/UxmlSerializedData")
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1] if st_nodes else []

for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
    chunk = raw[abs_off : abs_off + bsize]
    pat = b"StreamedTable/UxmlSerializedData"
    idx = 0
    while True:
        idx = chunk.find(pat, idx)
        if idx == -1:
            break
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if ln < 200 else f"Obj_{oi}"
        p = idx + 64
        print(f"\n--- Obj {oi} ({name}, pid={pid}) StreamedTable at +{idx} ---")
        for c in top_children:
            cname = st_nodes[c][3]
            try:
                p_next, val = walk_tree(st_nodes, chunk, p, c)
                if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                    print(f"  +0x{p - (idx+64):03x} {cname}: {val}")
                p = p_next
            except Exception as e:
                print(f"  ERROR at {cname}: {e}")
                break
        idx += len(pat)
