import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

print("=== 1. Disassemble Deserialize & Remaining StreamedTable Methods ===")
targets = [
    ("StreamedListView.UxmlSerializedData.Deserialize", 0x015b0b50, 0x015b1500),
    ("StreamedTable.UxmlSerializedData.Deserialize_Part2", 0x015f3900, 0x015f4200),
    ("StreamedTable_0x015f1100_to_0x015f36b0", 0x015f1100, 0x015f2400),
    ("StreamedTable_0x015f2400_to_0x015f36b0", 0x015f2400, 0x015f36b0),
    ("StreamedListView_0x015a5600_to_0x015a6000", 0x015a5600, 0x015a6000),
]
for name, s, e in targets:
    dhf.dump_fast(name, s, e)

print("\n=== 2. Check All VTA Objects in ui-recruitment_assets_all.bundle with 'Priorit' or 'Scout' ===")
raw_r, trees_r, objs_r, _ = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    cname, nodes = trees_r[tid]
    if cname != "MonoBehaviour":
        continue
    chunk = raw_r[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    name = val.get("m_Name") or val.get("common_427") or ""
    if any(k in str(name) for k in ("Priorit", "Scout", "Recruitment", "Focus", "Assignment")):
        veas = val.get("m_VisualElementAssets", [])
        trefs = val.get("m_TemplateAssets", [])
        st_types = [v.get("m_FullTypeName") for v in veas if "Table" in str(v.get("m_FullTypeName")) or "List" in str(v.get("m_FullTypeName"))]
        t_names = [t.get("m_TemplateAlias") for t in trefs]
        print(f"  Obj {oi:3d} (pid={pid}): {name} | Tables/Lists={st_types} | Templates={t_names}")
