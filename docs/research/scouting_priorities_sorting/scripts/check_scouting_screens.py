import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from compare_all_aspects import parse_bundle, walk_tree

res = parse_bundle("ui-recruitment_assets_all.bundle")
for oi in res["objs"]:
    d = walk_tree(res, oi)
    if isinstance(d, dict) and "m_Name" in d and d["m_Name"]:
        print(f"Obj {oi['index']:4d} (cls={oi['class_id']}): {d['m_Name']}")
