import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

for bname in ["ui-recruitment_assets_all.bundle", "ui-tiles_assets_all.bundle"]:
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]
    print(f"================ {bname} ================")
    for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
        chunk = raw[abs_off : abs_off + bsize]
        pat = b"StreamedTable/UxmlSerializedData"
        idx = chunk.find(pat)
        if idx != -1:
            ln = struct.unpack_from("<I", chunk, 28)[0]
            name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
            pos = idx
            while pos != -1:
                p = pos + 64
                vals = {}
                for c in top_children:
                    cname = st_nodes[c][3]
                    try:
                        p_next, val = walk_tree(st_nodes, chunk, p, c)
                        vals[cname] = val
                        p = p_next
                        if cname == "references":
                            break
                    except Exception:
                        break
                b_path = vals.get("Binding", {}).get("m_direct", {}).get("Path", {}).get("m_path", "")
                b_kind = vals.get("Binding", {}).get("m_kind", 0)
                sb_path = vals.get("SortBinding", {}).get("m_path", "")
                dis_sort = vals.get("DisableSorting", 0)
                reord = vals.get("Reorderable", 0)
                drag_cell = vals.get("DragCellID", "")
                drag_ev = len(vals.get("DragEvents", {}).get("m_bytes", []))
                fact = vals.get("FactoryAsset", {}).get("m_AssetGUID", "")
                sort_col = vals.get("SortedColumn", "")
                print(f"  Obj {oi:3d} ({name:44s}): Bind='{b_path}' (k={b_kind}) SortBind='{sb_path}' DisSort={dis_sort} Reord={reord} DragCell='{drag_cell}' DragEv={drag_ev} SortCol='{sort_col}' Fact={fact[:8]}")
                pos = chunk.find(pat, pos + 64)
