import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")

for oi, pid, abs_off, bsize, tid in objs:
    if tid >= len(trees):
        continue
    class_id, nodes = trees[tid]
    chunk = raw[abs_off : abs_off + bsize]
    try:
        _, d = walk_tree(nodes, chunk, 0, 0)
    except Exception as e:
        continue
    if not isinstance(d, dict) or "m_columns" not in d:
        continue
    name = d.get("common_0", d.get("m_Name", f"Obj_{oi}"))
    params = d.get("m_parameters", [])
    cols = d.get("m_columns", [])
    overrides = []
    for c in cols:
        cid = c.get("m_id", "")
        so = c.get("m_sortingOverride", {}).get("m_path", "")
        sv = c.get("m_sortingValue", 0)
        if so or sv:
            overrides.append((cid, so, sv))
    if any(k in str(name) for k in ("Scout", "Player", "Person", "Team", "Shortlist", "Priority", "Transfer")):
        print(f"Obj {oi:3d} ({str(name):45s}): params={params} total_cols={len(cols)} with_sort={len(overrides)}")
        for cid, so, sv in overrides[:12]:
            print(f"    {cid:35s} -> m_sortingOverride={so!r:35s} m_sortingValue={sv}")
