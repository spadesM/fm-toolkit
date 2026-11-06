import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Dump SpecificallyScoutedPersonReference methods before 0x00696f00
dump_fast('SpecificallyScoutedPersonReference_before_696f00', 0x00696600, 0x00696f10)

# 2. Check all factories in ui-tablefactories_assets_all.bundle
raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
print("\n=== ALL TABLE FACTORIES ===")
for oi, (idx, pid, abs_off, bsize, tid) in enumerate(objs_f):
    cid, nodes = trees_f[tid]
    if not nodes:
        continue
    chunk = raw_f[abs_off : abs_off + bsize]
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
    except Exception:
        continue
    if isinstance(val, dict) and "m_rowData" in val:
        name = val.get("common_427") or val.get("m_Name") or ""
        params = [(p.get("name"), p.get("type", {}).get("id")) for p in val.get("m_parameters", [])]
        rows = val.get("m_rowData", [])
        sorts = [(r.get("m_id"), r.get("m_sortBinding", {}).get("m_path"), r.get("m_sortBindingPlugin")) for r in rows if r.get("m_sortBinding", {}).get("m_path")]
        print(f"Obj {oi:3d} pid={pid:20d} name={name:45s} params={params[:2]} sorts={len(sorts)}/{len(rows)} sample={sorts[:2]}")
