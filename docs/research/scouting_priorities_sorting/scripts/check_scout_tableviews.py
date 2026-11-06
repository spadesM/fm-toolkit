import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")

for oi in (236, 400, 766, 791):
    _, pid, abs_off, bsize, tid = objs[oi]
    _, nodes = trees[tid]
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    p = abs_off
    print(f"\n==================== ui-tableviews Obj {oi} (pid={pid}, size={bsize}) ====================")
    for c in top_children:
        cname = nodes[c][3]
        p_next, val = walk_tree(nodes, raw, p, c)
        print(f"  {cname}: {val}")
        p = p_next
