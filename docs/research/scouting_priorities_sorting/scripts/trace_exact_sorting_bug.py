import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Search for VirtualisedList.m_reorderable (+0x5c1) across all VirtualisedList methods (0x016a7000..0x016ae000)
off_start = va_to_off(image_base + 0x016a7000)
off_end = va_to_off(image_base + 0x016ae000)
chunk = pe[off_start:off_end]
pos = 0
while True:
    idx = chunk.find(b"\xc1\x05\x00\x00", pos)
    if idx == -1:
        break
    rva = 0x016a7000 + idx
    # Find enclosing function
    fn_rva = max((k for k in rva_to_end if k <= rva), default=0)
    print(f"Found +0x5c1 at RVA=0x{rva:08x} in {rva_to_method_name.get(fn_rva)} (0x{fn_rva:08x})")
    pos = idx + 1

# 2. List all factories in ui-tablefactories_assets_all.bundle
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs:
    _, nodes = trees[tid]
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
    if "m_rowData" in props:
        rds = props.get("m_rowData", [])
        if any(w in name for w in ("Scout", "Player", "Person", "Team", "Recruitment", "Shortlist")):
            print(f"Factory Obj {oi:3d} ({name:45s}): params={len(props.get('m_parameters', []))} rowData={len(rds)} ctxPath={props.get('m_contextMenuBindingPath')}")
            if "SpecificallyScouted" in name:
                print(f"  m_parameters: {props.get('m_parameters')}")
                for rd in rds:
                    print(f"    id={rd.get('m_id'):22s} sort={rd.get('m_sortBinding', {}).get('m_path')!r:65s} asc={rd.get('m_sortAscending')} valBinds={[(vb.get('from'), vb.get('to', {}).get('m_path'), vb.get('type')) for vb in rd.get('m_valueBindings', [])]}")
