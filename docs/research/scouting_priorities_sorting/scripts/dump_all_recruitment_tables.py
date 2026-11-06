import struct
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
    chunk = raw[abs_off : abs_off + bsize]
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    if idx != -1:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        print(f"\n==================== Obj {oi} ({name}) ====================")
        pos = idx
        while pos != -1:
            p = pos + 64
            print(f"  --- Table at offset {p} ---")
            for c in top_children:
                cname = st_nodes[c][3]
                try:
                    p_next, val = walk_tree(st_nodes, chunk, p, c)
                    if cname == "references":
                        p = p_next
                        break
                    if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                        if cname in ("InitFunction", "BindFunction"):
                            print(f"    {cname}: target={val.get('m_target', {}).get('m_AssetGUID')}")
                        else:
                            print(f"    {cname}: {val}")
                    p = p_next
                except Exception as e:
                    print(f"    ERROR at {cname}: {e}")
                    break
            pos = chunk.find(pat, pos + 64)
