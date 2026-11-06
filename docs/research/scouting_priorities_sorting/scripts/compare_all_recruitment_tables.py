import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

pat = b"StreamedTable/UxmlSerializedData"
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
    chunk = raw[abs_off : abs_off + bsize]
    if pat not in chunk:
        continue
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if ln < 200 else f"Obj_{oi}"
    pos = 0
    t_idx = 0
    while True:
        idx = chunk.find(pat, pos)
        if idx == -1:
            break
        p = idx + 64
        print(f"\n==================== Obj {oi} ({name}) [#{t_idx}] ====================")
        for c in top_children[:-1]:
            cname = st_nodes[c][3]
            try:
                p_next, val = walk_tree(st_nodes, chunk, p, c)
            except Exception as e:
                print(f"  ERR at {cname}: {e}")
                break
            if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2, -1, -1.0):
                print(f"  +0x{p - (idx+64):03x} {cname}: {val}")
            p = p_next
        pos = idx + 64
        t_idx += 1
