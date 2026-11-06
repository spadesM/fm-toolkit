import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

print("All top-level fields of StreamedTable/UxmlSerializedData:")
for i, c in enumerate(top_children):
    print(f"  {i:3d}: {st_nodes[c][3]} ({st_nodes[c][2]})")

for oi in (229, 263, 111, 279, 360, 103):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    if idx != -1:
        p = idx + 64
        print(f"\n==================== Obj {oi} ({name}) ====================")
        for c in top_children[:-1]:
            cname = st_nodes[c][3]
            p_next, val = walk_tree(st_nodes, chunk, p, c)
            if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2, -1, -1.0):
                print(f"  +0x{p - (idx+64):03x} {cname}: {val}")
            p = p_next
