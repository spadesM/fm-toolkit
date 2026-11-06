import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\all_clues_table_and_list.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Dump remaining part of StreamedTable.BindToDataInternal and other StreamedTable methods ===")
rva_btd = 0x015e6d70
end_btd = rva_to_end.get(rva_btd, rva_btd + 3500)
dump_func_details("StreamedTable.BindToDataInternal (part 2)", rva_btd + 1800, end_btd - (rva_btd + 1800))

other_st_methods = [
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640),
    ("StreamedTable.UpdateSortColumn", 0x015f1380),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
    ("Bindings.Create", 0x014bf980),
    ("Bindings.Bind", 0x014bee30),
]
for label, rva in other_st_methods:
    sz = min(rva_to_end.get(rva, rva + 1500) - rva, 2000)
    dump_func_details(label, rva, sz)

print("\n=== 2. Check all VisualTreeAssets in ui-recruitment_assets_all.bundle mentioning Scout or Priorit or Ongoing or Assignment ===")
raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_r:
    chunk = raw_r[abs_off : abs_off + bsize]
    tname, nodes = trees_r[tid]
    if tname == "VisualTreeAsset":
        try:
            _, props = walk_tree(nodes, chunk, 0, 0)
            nm = props.get("m_Name", props.get("common_427", ""))
            if any(w in nm for w in ("Scout", "Priorit", "Assignment", "Recruitment", "Recommend", "Shortlist", "Focus")):
                print(f"  Obj {oi}: name={nm!r} (pid={pid}, size={bsize})")
        except Exception as e:
            pass

out_file.close()
