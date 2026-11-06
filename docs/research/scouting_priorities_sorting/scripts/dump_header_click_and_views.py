import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\header_click_and_views_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Inspect ui-tableviews_assets_all.bundle objects 236, 766, 400, 791 ===")
raw_v, trees_v, objs_v, ref_trees_v = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi in (236, 766, 400, 791):
    idx, pid, abs_off, bsize, tid = objs_v[oi]
    chunk = raw_v[abs_off : abs_off + bsize]
    tname, nodes = trees_v[tid]
    print(f"\n--- Obj {oi} (pid={pid}, tid={tid} ({tname}), size={bsize}) ---")
    try:
        _, props = walk_tree(nodes, chunk, 0, 0)
        for k, v in props.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"  walk_tree error: {e}")
        # print top-level node names
        for ni, n in enumerate(nodes[:30]):
            print(f"    node {ni}: {n}")

# Also find Shortlist table views in ui-tableviews_assets_all.bundle
for oi, pid, abs_off, bsize, tid in objs_v:
    chunk = raw_v[abs_off : abs_off + bsize]
    if b"Shortlist" in chunk or b"ScoutPriorities" in chunk:
        tname, nodes = trees_v[tid]
        try:
            _, props = walk_tree(nodes, chunk, 0, 0)
            nm = props.get("m_Name", props.get("common_427", ""))
            print(f"\nFound View Obj {oi} (pid={pid}, name={nm!r}, tname={tname}):")
            for k, v in props.items():
                if k != "m_Script":
                    print(f"  {k}: {v}")
        except Exception as e:
            print(f"Found View Obj {oi} error: {e}")

print("\n=== 2. Dump StreamedTable header/sorting/column methods ===")
methods_to_dump = [
    ("StreamedTable.OnHeaderClicked", 0x15ec910),
    ("StreamedTable.BindHeader", 0x15e6230),
    ("StreamedTable.CreateHeader", 0x15e8f00),
    ("StreamedTable.MakeColumnHeader", 0x15eac30),
    ("StreamedTable.CreateColumn", 0x15e7dc0),
    ("StreamedTable.CreateColumnsFromTableView", 0x15e8350),
    ("StreamedTable.CreateColumnsFromTableViewCollection", 0x15e82c0),
    ("StreamedTable.OnSortColumn", 0x15ee250),
    ("StreamedTable.ApplyPersistedSortingState", 0x15e58c0),
    ("StreamedTable.SetList", 0x15ef610),
    ("StreamedTable.RebuildInternal", 0x15ee9c0),
    ("StreamedTable.RefreshInternal", 0x15eed80),
    ("StreamedTable.SetNoSorting", 0x15ef750),
    ("StreamedTable.UpdateSortColumn", 0x15f1380),
    ("Bindings.HashPath", 0x14c1d40),
    ("Bindings.MixHash", 0x14c2500),
]

for label, rva in methods_to_dump:
    sz = min(rva_to_end.get(rva, rva + 512) - rva, 1500)
    dump_func_details(label, rva, sz)

out_file.close()
