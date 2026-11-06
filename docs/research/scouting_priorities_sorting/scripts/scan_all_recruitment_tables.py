import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from inspect_all_vta_props import parse_bundle_with_reftypes, walk_tree

def find_all_streamed_tables(bundle_name):
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bundle_name)
    print(f"=== {bundle_name}: scanning {len(objs)} objects ===")
    for i, pid, abs_off, bsize, tid in objs:
        cname, root = trees[tid]
        if cname != "VisualTreeAsset":
            continue
        b = raw[abs_off:abs_off+bsize]
        _, vta = walk_tree(root, b, 0, 0)
        name = vta.get("m_Name", "")
        uxml = vta.get("m_UxmlObjectEntries", [])
        refs = vta.get("m_serializedDataReferences", [])
        
        # check if any ref is StreamedTable
        for r in refs:
            rc = r.get("referencedObject", {}).get("class", "")
            if "StreamedTable" in rc:
                data_bytes = r.get("referencedObject", {}).get("data", b"")
                ref_tree = ref_trees.get((r["referencedObject"]["class"], r["referencedObject"]["ns"], r["referencedObject"]["asm"]))
                if ref_tree:
                    _, d = walk_tree(ref_tree, data_bytes, 0, 0)
                    b_path = d.get("m_binding", {}).get("m_path", "")
                    sb_path = d.get("m_sortBinding", {}).get("m_path", "")
                    s_col = d.get("m_sortedColumn", {}).get("m_path", "")
                    s_dir = d.get("m_sortingDirection", {}).get("m_path", "")
                    sec_col = d.get("m_secondarySortedColumn", {}).get("m_path", "")
                    dis_sort = d.get("m_disableSorting", 0)
                    reord = d.get("m_reorderable", 0)
                    drag_id = d.get("m_dragCellID", "")
                    fac = d.get("m_factoryAsset", {})
                    tvs = d.get("m_tableViewsAsset", {})
                    tv = d.get("m_tableViewAsset", {})
                    print(f"  Obj {i} ({name}):")
                    print(f"    m_binding='{b_path}'")
                    print(f"    m_sortBinding='{sb_path}', m_sortedColumn='{s_col}', m_sortingDirection='{s_dir}', m_secondarySortedColumn='{sec_col}'")
                    print(f"    m_disableSorting={dis_sort}, m_reorderable={reord}, m_dragCellID='{drag_id}'")
                    print(f"    factory={fac.get('m_PathID')}, views={tvs.get('m_PathID')}, view={tv.get('m_PathID')}")

find_all_streamed_tables("ui-recruitment_assets_all.bundle")
