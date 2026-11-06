import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

bundles = [
    "ui-panelids-uxml_assets_all.bundle",
    "ui-tiles_assets_all.bundle",
    "ui-tileslayouts_assets_all.bundle",
    "ui-columns_assets_all.bundle",
    "ui-recruitment_assets_all.bundle",
]

for bname in bundles:
    print(f"\n==================== {bname} ====================")
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    st_nodes = ref_trees.get("StreamedTable/UxmlSerializedData")
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1] if st_nodes else []
    for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
        chunk = raw[abs_off : abs_off + bsize]
        if b"ScoutPriorities" in chunk or b"SpecificallyScouted" in chunk:
            cid, nodes = trees[tid]
            # Try to get m_Name
            name = ""
            if len(nodes) > 1 and nodes[1][3] in ("m_Name", "common_427"):
                try:
                    _, name = walk_tree(nodes, chunk, 0, 1)
                except Exception:
                    pass
            print(f"  Obj {oi} (cid={cid}, pid={pid}, size={bsize}): name={name!r}")
            # Find strings containing ScoutPriorities or SpecificallyScouted
            for kw in (b"ScoutPriorities", b"SpecificallyScouted"):
                pos = chunk.find(kw)
                while pos != -1:
                    s_start = max(0, pos - 32)
                    s_end = min(len(chunk), pos + 64)
                    ascii_s = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[s_start:s_end])
                    print(f"    @{pos}: {ascii_s}")
                    pos = chunk.find(kw, pos + 1)
            # If it has StreamedTable/UxmlSerializedData, parse it!
            if st_nodes:
                pat = b"StreamedTable/UxmlSerializedData"
                tpos = chunk.find(pat)
                while tpos != -1:
                    p = tpos + 64
                    print(f"    --- StreamedTable at +{p} ---")
                    for c in top_children:
                        cname = st_nodes[c][3]
                        if cname == "references":
                            break
                        try:
                            p_next, val = walk_tree(st_nodes, chunk, p, c)
                            if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                                print(f"      {cname}: {val}")
                            p = p_next
                        except Exception as e:
                            print(f"      ERR at {cname}: {e}")
                            break
                    tpos = chunk.find(pat, tpos + 64)
