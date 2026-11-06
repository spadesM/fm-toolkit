import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

print("=== 1. Dump StreamedListView.OnSortColumnStateEvent & StreamedListView.Sort ===")
targets = [
    ("OnSortColumn_and_SortByColumn", 0x015a9a80, 0x015a9d00),
    ("StreamedListView.Sort", 0x015aa750, 0x015aaa70),
    ("StreamedTable.SortByColumn_Internal", 0x015e58c0, 0x015e6230),
    ("StreamedTable.OnSortColumn_Shortcut", 0x015ec910, 0x015ece00),
]
for name, s, e in targets:
    dhf.dump_fast(name, s, e)

print("\n=== 2. All VTAs in ui-recruitment_assets_all.bundle with Tables/Lists or 'Priorit'/'Scout' ===")
raw_r, trees_r, objs_r, _ = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    cname, nodes = trees_r[tid]
    chunk = raw_r[abs_off : abs_off + bsize]
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
    except Exception:
        continue
    if not isinstance(val, dict):
        continue
    name = val.get("m_Name") or val.get("common_427") or ""
    veas = val.get("m_VisualElementAssets") or val.get("common_452") or []
    trefs = val.get("m_TemplateAssets") or val.get("common_450") or []
    if not veas and not trefs:
        continue
    st_types = []
    for v in veas:
        ft = v.get("m_FullTypeName") or v.get("common_468") or ""
        vn = v.get("m_Name") or v.get("common_427") or ""
        vid = v.get("m_Id") or v.get("common_465") or 0
        if "Table" in str(ft) or "List" in str(ft):
            st_types.append((vid, ft, vn))
    t_names = [t.get("m_TemplateAlias") or t.get("common_453") for t in trefs]
    if st_types or any(k in str(name) for k in ("Priorit", "Scout", "Focus", "Assignment")):
        print(f"  Obj {oi:3d} (pid={pid}): {name}")
        if st_types:
            print(f"    Tables/Lists: {st_types}")
        if t_names:
            print(f"    Templates: {t_names}")
