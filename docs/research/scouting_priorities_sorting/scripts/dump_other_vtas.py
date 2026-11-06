import sys
sys.stdout.reconfigure(encoding="utf-8")
from inspect_vta_refs_and_props import raw, objs, trees, walk_tree, dump_vta_refs

for oi in (85, 210, 301, 367):
    dump_vta_refs(oi)
