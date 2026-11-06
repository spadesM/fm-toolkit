import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

raw_tf, trees_tf, objs_tf, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
ptf_map = {}
spec_cols = []
for oi, pid, abs_off, bsize, tid in objs_tf:
    if pid in (-2280246386909779364, -6813643292728705340):
        chunk = raw_tf[abs_off : abs_off + bsize]
        _, val = walk_tree(trees_tf[tid][1], chunk, 0, 0)
        name = val.get("common_427")
        cols = val.get("m_rowData", [])
        print(f"=== {name}: {len(cols)} columns | emitIndex={val.get('m_emitIndexBinding')} | params={val.get('m_parameters')} ===")
        if name == "PlayerTableFactory":
            ptf_map = {c.get("m_id"): c for c in cols}
        else:
            spec_cols = cols

sp_cols = {'inf', 'player-nationality', 'age', 'club-division', 'position', 'recommendation', 'staff', 'assignment-type', 'value'}
print("\n--- Columns used in ScoutPrioritiesTable ---")
for c in spec_cols:
    cid = c.get("m_id")
    if cid in sp_cols:
        s1 = c.get("m_sortBinding", {}).get("m_path")
        vb1 = [(b.get("from"), b.get("to", {}).get("m_path")) for b in c.get("m_valueBindings", [])]
        pc = ptf_map.get(cid, {})
        s2 = pc.get("m_sortBinding", {}).get("m_path", "<N/A>")
        print(f"  [{cid}] sort='{s1}' (PlayerTF='{s2}') plugin={c.get('m_sortBindingPlugin')} asc={c.get('m_sortAscending')} vb={vb1}")

print("\n--- All columns in SpecificallyScoutedPersonTableFactory with empty sortBinding ---")
for c in spec_cols:
    cid = c.get("m_id")
    s1 = c.get("m_sortBinding", {}).get("m_path")
    if not s1:
        vb1 = [(b.get("from"), b.get("to", {}).get("m_path")) for b in c.get("m_valueBindings", [])]
        print(f"  [{cid}] sort='{s1}' | vb={vb1}")

for name, rva in [
    ("ScoutAssignmentsReference.GetPropertiesInternal", 0x0067c1c0),
    ("ScoutAssignmentsReference.GetPropertyTypeInternal", 0x0067c450),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("SpecificallyScoutedPersonReference.DerivesFromInternal", 0x00696f50),
]:
    dhf.dump_fast(name, rva)
