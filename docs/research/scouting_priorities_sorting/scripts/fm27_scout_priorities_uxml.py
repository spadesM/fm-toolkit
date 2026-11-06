import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
sys.stdout.reconfigure(encoding="utf-8")
import struct
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

SKIP_DEFAULTS = (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0},
                 {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0})
for bname in sys.argv[1:]:
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    if "StreamedTable/UxmlSerializedData" not in ref_trees:
        print("no ST reftype in", bname); continue
    st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]
    for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
        chunk = raw[abs_off: abs_off + bsize]
        if b"ScoutPriorities.SpecificallyScoutedPlayers" not in chunk:
            continue
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32:32 + ln].decode("utf-8", "replace") if 0 < ln < 200 else "?"
        pos = 0
        while True:
            idx = chunk.find(b"StreamedTable/UxmlSerializedData", pos)
            if idx < 0: break
            pos = idx + 1
            p = idx + 64
            print(f"\n=== {bname} Obj {oi} {name} pid={pid} size={bsize} ST@abs {abs_off+idx:#x} ===")
            for c in top_children:
                cname = st_nodes[c][3]
                if cname == "references": break
                start = p
                try:
                    p, val = walk_tree(st_nodes, chunk, p, c)
                except Exception as e:
                    print("ERR", cname, e); break
                if cname.endswith("_UxmlAttributeFlags") or val in SKIP_DEFAULTS: continue
                s = str(val)
                print(f"  [{abs_off+start:#x}] {cname}: {s[:260]}")
