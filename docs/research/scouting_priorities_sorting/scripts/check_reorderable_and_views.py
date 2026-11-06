import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, types_off, types_sz, methods_off, fields_off, fields_sz, get_mstr,
    va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details, modules
)
from annotate_sorting_usym import dump_annotated
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Print all fields and offsets of StreamedListView, StreamedObjectList, StreamedTable
# Field offsets in Il2Cpp are stored in Il2CppCodeRegistration / fieldOffsets array in PE, or we can check getter/setter methods!
print("=== Getters/Setters on StreamedListView / StreamedTable ===")
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(n.startswith(p) for p in ("StreamedListView.get_", "StreamedListView.set_", "StreamedObjectList.get_", "StreamedObjectList.set_", "StreamedTable.get_", "StreamedTable.set_")):
            off = va_to_off(image_base + rva)
            code = pe[off : off + 32]
            print(f"  0x{rva:08x} {n}: {code[:16].hex(' ')}")

# 2. Check StreamedTable.CanPopulateTable, MakeColumnHeader, CreateColumn, BindHeader, OnHeaderClicked, SetSorting, get_IsDragCellActive, OnStartReorder, OnReorder, OnEndReorder
for name, rva in [
    ("StreamedTable.CanPopulateTable", 0x015e7640),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.get_IsDragCellActive", 0x015f2230),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedTable.UpdatePersistedColumnSortingData", 0x015f1290),
    ("StreamedTable.GeneratePersistenceKeys", 0x015e9600),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)

# 3. Inspect ui-tableviews_assets_all.bundle properly (find the name field in TypeTree)
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
print("\n=== TypeTrees in ui-tableviews_assets_all.bundle ===")
for ti, (cid, nodes) in enumerate(trees):
    if nodes:
        print(f"  Tree {ti} (cid={cid}): root={nodes[0][2]} children={[n[3] for n in nodes if n[0]==1]}")

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
        # find any string value that looks like a name
        first_strs = [v for k, v in val.items() if isinstance(v, str)]
        name = first_strs[0] if first_strs else ""
        if any(k in name.lower() for k in ("scoutpriorit", "recommendation", "shortlist")):
            print(f"\n--- Obj {oi} [PathID {pid}] ({nodes[0][2]}) name={name!r} ---")
            for k, v in val.items():
                if k in ("m_Script", "m_GameObject", "m_Enabled") or k.startswith("common_"):
                    if isinstance(v, str):
                        print(f"  {k}: {v!r}")
                    continue
                if k == "m_contextMenuData" and isinstance(v, list):
                    print(f"  m_contextMenuData: ({len(v)} items) first 5={v[:5]}")
                else:
                    print(f"  {k}: {v}")
