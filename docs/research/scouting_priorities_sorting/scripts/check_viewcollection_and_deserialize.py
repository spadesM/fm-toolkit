import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
from check_deep_sorting import rva_to_method_name, dump_func_details

# 1. Inspect Obj 236, 766, 791 in ui-tableviews_assets_all.bundle
raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_v:
    chunk = raw_v[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0] if bsize >= 36 else 0
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else ""
    if "ScoutPriorit" in name or oi in (236, 766, 791):
        _, nodes = trees_v[tid]
        _, val = walk_tree(nodes, chunk, 0, 0)
        print(f"\n=== ui-tableviews Obj {oi} (pid={pid}, name={name}) ===")
        print(val)

# 2. Find UxmlSerializedData.Deserialize for StreamedListView and StreamedTable
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if ("StreamedListView" in n or "StreamedTable" in n) and ("UxmlSerializedData" in n or "Deserialize" in n or "Reorderable" in n or "Init" in n):
            print(f"  0x{rva:08x}: {n}")
