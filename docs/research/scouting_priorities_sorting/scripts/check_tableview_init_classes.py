import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import (
    pe, meta, types_off, types_sz, methods_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Dump all methods of Type 6093, 6094, 6095, 6100, 6298, 6299, 6300
for ti in (6093, 6094, 6095, 6100, 6298, 6299, 6300):
    toff = types_off + ti * 88
    tu = struct.unpack_from("<22I", meta, toff)
    tname = get_mstr(tu[0])
    mstart = tu[9]
    mcount = tu[16] & 0xFFFF
    print(f"\n=== Type [{ti}] {tname} (methods={mcount}) ===")
    for mi in range(mstart, mstart + mcount):
        moff = methods_off + mi * 36
        mname_idx = struct.unpack_from("<I", meta, moff)[0]
        mname = get_mstr(mname_idx)
        for rva, names in rva_to_method_name.items():
            if f"{tname}.{mname}" in names:
                print(f"  0x{rva:08x}: {tname}.{mname}")
                dump_annotated(f"{tname}.{mname}", rva)
                dump_func_details(f"{tname}.{mname}", rva)

# 2. Compare ScoutPrioritiesTableViewCollection / ScoutPrioritiesTable with working ones in ui-tableviews_assets_all.bundle
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
print(f"\n=== ui-tableviews_assets_all.bundle objects (total={len(objs)}) ===")
for oi, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    if not nodes:
        continue
    chunk = raw[abs_off : abs_off + bsize]
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
    except Exception:
        continue
    if isinstance(val, dict):
        name = val.get("m_Name", "")
        if any(k in name.lower() for k in ("scoutpriorit", "recommendation", "shortlist", "playersearch", "playerdatabase")):
            print(f"\n--- Obj {oi} [PathID {pid}] ({nodes[0][2]}) {name} ---")
            for k, v in val.items():
                if k in ("m_Script", "m_GameObject", "m_Enabled"):
                    continue
                print(f"  {k}: {v}")
