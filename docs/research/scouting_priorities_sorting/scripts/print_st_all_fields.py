import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]
for oi in (229, 111):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    idx = chunk.find(b"StreamedTable/UxmlSerializedData")
    p = idx + 64
    print(f"===== Obj {oi} =====")
    for c in top_children:
        cname = st_nodes[c][3]
        if cname == "references": break
        start = p
        p, val = walk_tree(st_nodes, chunk, p, c)
        s = str(val)
        if len(s) > 120: s = s[:120] + "..."
        print(f"  [{abs_off+start:#x}] {cname} ({st_nodes[c][2]}): {s}")
