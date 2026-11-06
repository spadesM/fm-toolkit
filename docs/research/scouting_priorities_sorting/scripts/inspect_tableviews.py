import sys, pprint
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
print("Total objs:", len(objs))
for idx in (236, 400, 766, 791, 10, 20):
    i, pid, abs_off, bsize, tid = objs[idx]
    chunk = raw[abs_off : abs_off + bsize]
    class_id, nodes = trees[tid]
    print(f"\n--- Obj {i} (PathID={pid}, tid={tid}, class={class_id}, nodes={len(nodes)}) ---")
    for ni, n in enumerate(nodes[:25]):
        print(f"  node[{ni}]: {n}")
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
        pprint.pprint(val, width=140)
    except Exception as e:
        print("walk_tree error:", e)
