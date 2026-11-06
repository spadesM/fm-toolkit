import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

print("=== 1. All VisualTreeAssets in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, _ = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    cname, nodes = trees_r[tid]
    if cname != "VisualTreeAsset":
        continue
    chunk = raw_r[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    name = val.get("m_Name") or val.get("common_427") or ""
    veas = val.get("m_VisualElementAssets", [])
    trefs = val.get("m_TemplateAssets", [])
    st_types = [(v.get("m_Id"), v.get("m_FullTypeName"), v.get("m_Name")) for v in veas if "Table" in str(v.get("m_FullTypeName")) or "List" in str(v.get("m_FullTypeName"))]
    t_names = [t.get("m_TemplateAlias") for t in trefs]
    if st_types or any(k in str(name) for k in ("Priorit", "Scout", "Focus", "Assignment")):
        print(f"  Obj {oi:3d} (pid={pid}): {name}")
        if st_types:
            print(f"    Tables/Lists: {st_types}")
        if t_names:
            print(f"    Templates: {t_names}")

print("\n=== 2. Dump Sort Methods with USYM ===")
targets = [
    ("MakeColumnHeader_b__0", 0x0160bb80, 0x0160bd00),
    ("StreamedTable.SortByColumn", 0x015efc30, 0x015f0040),
    ("StreamedTable.SetDefaultSorting", 0x015f0040, 0x015f0230),
    ("StreamedListView.SortByColumn", 0x015a9cb0, 0x015aa320),
    ("StreamedListView.ApplySorting", 0x015a4260, 0x015a4850),
    ("StreamedListView.Sort", 0x015aaa70, 0x015aae00),
]
for name, s, e in targets:
    dhf.dump_fast(name, s, e)
