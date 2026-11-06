import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes

def walk_vta(nodes, data, pos, node_idx=0):
    lvl, tflags, tname, nname, bsz, mflag = nodes[node_idx]
    children = []
    i = node_idx + 1
    while i < len(nodes) and nodes[i][0] > lvl:
        if nodes[i][0] == lvl + 1:
            children.append(i)
        i += 1
    if tname == "common_840" or tname == "string":
        slen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        sval = data[pos : pos + slen].decode("utf-8", errors="replace")
        pos += slen
        pos = (pos + 3) & ~3
        return pos, sval
    elif tflags & 1:
        cnt = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        elem_node = children[1]
        arr = []
        for _ in range(cnt):
            pos, ev = walk_vta(nodes, data, pos, elem_node)
            arr.append(ev)
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, arr
    elif not children:
        if bsz == 1:
            v = data[pos]
        elif bsz == 2:
            v = struct.unpack_from("<H", data, pos)[0]
        elif bsz == 4:
            if tname == "common_161" or tname == "float":
                v = round(struct.unpack_from("<f", data, pos)[0], 2)
            else:
                v = struct.unpack_from("<i", data, pos)[0]
        elif bsz == 8:
            v = struct.unpack_from("<q", data, pos)[0]
        else:
            v = data[pos : pos + bsz].hex()
        pos += bsz
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, v
    else:
        if len(children) == 1 and nodes[children[0]][3] in ("common_49", "Array"):
            pos, arr = walk_vta(nodes, data, pos, children[0])
            if mflag & 0x4000:
                pos = (pos + 3) & ~3
            return pos, arr
        obj = {}
        for c in children:
            c_name = nodes[c][3]
            c_type = nodes[c][2]
            if c_type == "ManagedReferencesRegistry" or c_name == "references":
                break
            pos, cv = walk_vta(nodes, data, pos, c)
            obj[c_name] = cv
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, obj

raw_tv, trees_tv, objs_tv, ref_trees_tv = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi in (236, 400, 766, 791):
    _, pid, abs_off, bsize, tid = objs_tv[oi]
    cname, nodes = trees_tv[tid]
    chunk = raw_tv[abs_off : abs_off + bsize]
    _, val = walk_vta(nodes, chunk, 0, 0)
    print(f"\n================ ui-tableviews Obj {oi} (pid={pid}) ================")
    for k, v in val.items():
        if isinstance(v, list):
            print(f"  {k}: list of {len(v)} items:")
            for item in v[:15]:
                print(f"    {item}")
        else:
            print(f"  {k}: {v}")

raw_tf, trees_tf, objs_tf, ref_trees_tf = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi in (92,):
    _, pid, abs_off, bsize, tid = objs_tf[oi]
    cname, nodes = trees_tf[tid]
    chunk = raw_tf[abs_off : abs_off + bsize]
    _, val = walk_vta(nodes, chunk, 0, 0)
    print(f"\n================ ui-tablefactories Obj {oi} (pid={pid}) ================")
    for k, v in val.items():
        if isinstance(v, list):
            print(f"  {k}: list of {len(v)} items:")
            for item in v:
                print(f"    {item}")
        else:
            print(f"  {k}: {v}")
