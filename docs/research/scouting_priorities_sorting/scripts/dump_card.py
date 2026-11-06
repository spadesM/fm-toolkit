import sys
sys.stdout.reconfigure(encoding="utf-8")
from inspect_vta_refs_and_props import raw, objs, trees, walk_tree, dump_vta_refs
import pprint

for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off:abs_off+bsize]
    if b"ScoutPriorities" in chunk or b"SpecificallyScouted" in chunk:
        _, nodes = trees[tid]
        p, name = walk_tree(nodes, raw, abs_off, 1)
        print(f"Found in Obj {oi} (pid={pid}, tid={tid}, name={name!r}, size={bsize})")

for oi in (177, 229, 263):
    _, pid, abs_off, bsize, tid = objs[oi]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {}
    for c in top_children:
        cname = nodes[c][3]
        if cname == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[cname] = val
    print(f"\n================ Obj {oi} ({res.get('common_427')}) ================")
    for k, v in res.items():
        if v:
            print(f"  {k}:")
            pprint.pprint(v, indent=4, width=120)
    dump_vta_refs(oi)
