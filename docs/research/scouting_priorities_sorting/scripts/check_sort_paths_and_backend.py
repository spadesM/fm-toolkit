import struct, sys, os

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sort_paths_and_backend_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Disassemble Hash Function 0x002ae590 ===")
dump_func_details("Hash_0x002ae590", 0x002ae590, 0x150)

print("\n=== 2. Disassemble StreamedTable.SetSorting, TrySetColumnsAndSort, SortComparer ===")
dump_func_details("StreamedTable.SetSorting", 0x015efc40, 0x400)
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x600)
dump_func_details("SortComparer", 0x015b12d0, 0x350)

print("\n=== 3. Find all methods of StreamedTable, PlayerReference, PersonReference, TeamReference ===")
for rva, mname in sorted(rva_to_method_name.items()):
    if any(k in mname for k in ("StreamedTable.", "PlayerReference.", "PersonReference.", "TeamReference.", "ScoutPriorities")):
        print(f"  0x{rva:08x}: {mname}")

print("\n=== 4. Inspect ui-tableviews_assets_all.bundle ===")
raw_v, trees_v, objs_v, ref_trees_v = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_v):
    chunk = raw_v[abs_off : abs_off + bsize]
    if tid in trees_v and len(chunk) >= 32:
        nodes = trees_v[tid]
        try:
            _, val = walk_tree(nodes, chunk, 0, 0)
            name = val.get("m_Name", "") if isinstance(val, dict) else ""
            if any(k in name for k in ("ScoutPriorities", "Shortlist", "PlayerDatabase", "PlayerSearch")):
                print(f"\n--- View Obj {oi} ({name}, pid={pid}, tid={tid}, size={bsize}) ---")
                for k, v in val.items():
                    if k not in ("m_Script",):
                        print(f"  {k}: {v}")
        except Exception as e:
            pass

out_file.close()
