import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

vals_by_obj = {}
for oi in (229, 263, 103, 111, 360):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    p = idx + 64
    d = {}
    for c in top_children:
        cname = st_nodes[c][3]
        if cname == "references": break
        p_next, val = walk_tree(st_nodes, chunk, p, c)
        d[cname] = val
        p = p_next
    vals_by_obj[f"{oi}:{name}"] = d

all_keys = list(vals_by_obj["229:ScoutPrioritiesBlock"].keys())
for k in all_keys:
    row_vals = {oname: vals_by_obj[oname].get(k) for oname in vals_by_obj}
    # Print if any object differs or if non-empty in 229
    first_val = next(iter(row_vals.values()))
    if any(v != first_val for v in row_vals.values()):
        print(f"DIFF {k}:")
        for oname, v in row_vals.items():
            print(f"  {oname:45s}: {v}")
