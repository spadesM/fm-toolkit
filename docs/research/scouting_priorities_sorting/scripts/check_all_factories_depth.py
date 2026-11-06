import os, sys, glob, struct
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree

# 1. Check all factories in ui-tablefactories_assets_all.bundle to see which ones have multi-depth m_sortBinding (more than 1 dot, e.g. binding.x.y)
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs:
    tname, nodes = trees[tid]
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    p = abs_off
    props = {}
    for c in top_children:
        cname = nodes[c][3]
        try:
            p_next, val = walk_tree(nodes, raw, p, c)
            props[cname] = val
            p = p_next
        except Exception:
            break
    if "m_rowData" in props:
        m_name = props.get("m_Name", f"Obj_{oi}")
        rows = props["m_rowData"]
        sorts = [r.get("m_sortBinding", {}).get("m_path", "") for r in rows if r.get("m_sortBinding", {}).get("m_path", "")]
        multi = [s for s in sorts if s.count(".") >= 2]
        single = [s for s in sorts if s.count(".") == 1]
        print(f"Factory Obj {oi:3d} ({m_name:45s}): cols={len(rows):3d}, single_depth={len(single):3d}, multi_depth={len(multi):3d} (e.g. {sorts[:2]})")
