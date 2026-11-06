import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Dump set_Reorderable and check what field offset it sets!
dump_func_details("StreamedListView.set_Reorderable", 0x015ad4f0)
dump_func_details("StreamedTable.OnStartReorder", 0x015ee350)
dump_func_details("StreamedTable.OnReorder", 0x015edbe0)
dump_func_details("StreamedTable.OnEndReorder", 0x015ec410)

# 2. Inspect all factories in ui-tablefactories_assets_all.bundle
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs:
    _, nodes = trees[tid]
    if not nodes or nodes[0][2] != "MonoBehaviour":
        continue
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
    name = props.get("common_427", "")
    if "Scout" in name or "Player" in name or "Recruitment" in name or "Person" in name:
        rds = props.get("m_rowData", [])
        print(f"Factory Obj {oi:3d} ({name:45s}): params={len(props.get('m_parameters', []))} rowData={len(rds)} ctxPath={props.get('m_contextMenuBindingPath')}")
        if len(rds) <= 20:
            for rd in rds:
                print(f"    id={rd.get('m_id'):22s} sort={rd.get('m_sortBinding', {}).get('m_path')!r:65s} asc={rd.get('m_sortAscending')} valBinds={[(vb.get('from'), vb.get('to', {}).get('m_path')) for vb in rd.get('m_valueBindings', [])]}")
