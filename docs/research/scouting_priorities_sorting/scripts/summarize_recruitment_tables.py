import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

pat = b"StreamedTable/UxmlSerializedData"
for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    if pat in chunk:
        ln = struct.unpack_from("<I", chunk, 28)[0] if bsize >= 32 else 0
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else f"obj_{oi}"
        pos = 0
        occ = 0
        while True:
            idx = chunk.find(pat, pos)
            if idx == -1:
                break
            occ += 1
            p = idx + 64
            props = {}
            for c in top_children:
                cname = st_nodes[c][3]
                try:
                    p_next, v = walk_tree(st_nodes, chunk, p, c)
                    props[cname] = v
                    p = p_next
                except Exception:
                    break
            bpath = props.get("Binding", {}).get("m_direct", {}).get("Path", {}).get("m_path", "")
            vf = props.get("Binding", {}).get("m_visualFunction", {}).get("m_target", {}).get("m_AssetGUID", "")
            init_fn = props.get("InitFunction", {}).get("m_target", {}).get("m_AssetGUID", "")
            fac = props.get("FactoryAsset", {}).get("m_AssetGUID", "")
            dis_sort = props.get("DisableSorting", 0)
            reord = props.get("Reorderable", 0)
            drag_cell = props.get("DragCellID", "")
            sort_col = props.get("SortedColumn", "")
            sort_bind = props.get("SortBinding", "")
            print(f"Obj {oi:3d} #{occ} ({name:45s}): bind={bpath or vf} | init={init_fn[:8]} | fac={fac[:8]} | disSort={dis_sort} | reord={reord} | dragCell={drag_cell!r} | sortCol={sort_col!r} | sortBind={sort_bind!r}")
            pos = idx + len(pat)
