import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
import dump_headers_fast as dhf

print("=== 1. Disassemble 0x015a9420..0x015a9a80 and 0x00abdcc0 ===")
for name, s, e in [
    ("StreamedListView_0x015a9420_to_0x015a9a80", 0x015a9420, 0x015a9a80),
    ("QueueStateEvent_0x00abdcc0", 0x00abdcc0, 0x00abdf00),
]:
    dhf.dump_fast(name, s, e)

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

print("\n=== 2. All VTAs in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    cname, nodes = trees_r[tid]
    node_names = [n[3] for n in nodes]
    if "m_VisualElementAssets" not in node_names and "common_452" not in node_names:
        continue
    chunk = raw_r[abs_off : abs_off + bsize]
    _, val = walk_vta(nodes, chunk, 0, 0)
    name = val.get("m_Name") or val.get("common_427") or ""
    veas = val.get("m_VisualElementAssets") or val.get("common_452") or []
    trefs = val.get("m_TemplateAssets") or val.get("common_450") or []
    st_types = []
    for v in veas:
        ft = v.get("m_FullTypeName") or v.get("common_468") or ""
        vn = v.get("m_Name") or v.get("common_427") or ""
        vid = v.get("m_Id") or v.get("common_465") or 0
        if "Table" in str(ft) or "List" in str(ft):
            st_types.append((vid, ft, vn))
    t_names = [t.get("m_TemplateAlias") or t.get("common_453") for t in trefs]
    if st_types or any(k in str(name) for k in ("Priorit", "Scout", "Focus", "Assignment", "Recruitment")):
        print(f"  Obj {oi:3d} (pid={pid}): {name}")
        if st_types:
            print(f"    Tables/Lists: {st_types}")
        if t_names:
            print(f"    Templates: {t_names}")

for oi in (229, 263, 177, 43):
    _, pid, abs_off, bsize, tid = objs_r[oi]
    cname, nodes = trees_r[tid]
    chunk = raw_r[abs_off : abs_off + bsize]
    _, val = walk_vta(nodes, chunk, 0, 0)
    name = val.get("m_Name") or val.get("common_427") or ""
    print(f"\n================ FULL VTA: Obj {oi} {name} (pid={pid}) ================")
    veas = val.get("m_VisualElementAssets") or val.get("common_452") or []
    trefs = val.get("m_TemplateAssets") or val.get("common_450") or []
    all_nodes = []
    for v in veas:
        all_nodes.append((
            v.get("m_Id") or v.get("common_465") or 0,
            v.get("m_ParentId") or v.get("common_467") or 0,
            v.get("m_OrderInDocument") or v.get("common_466") or 0,
            v.get("m_FullTypeName") or v.get("common_468") or "",
            v.get("m_Name") or v.get("common_427") or "",
            v.get("m_Classes") or v.get("common_471") or [],
            v.get("m_SerializedData")
        ))
    for t in trefs:
        all_nodes.append((
            t.get("m_Id") or t.get("common_465") or 0,
            t.get("m_ParentId") or t.get("common_467") or 0,
            t.get("m_OrderInDocument") or t.get("common_466") or 0,
            f"TEMPLATE:{t.get('m_TemplateAlias') or t.get('common_453')}",
            t.get("m_Name") or t.get("common_427") or "",
            t.get("m_Classes") or t.get("common_471") or [],
            t.get("m_SerializedData")
        ))
    all_nodes.sort(key=lambda x: x[2])
    id_to_children = {}
    for n in all_nodes:
        id_to_children.setdefault(n[1], []).append(n)
    def print_tree(parent_id, indent=0):
        for n in id_to_children.get(parent_id, []):
            nid, pid_, ord_, ftype, nname, classes, sdata = n
            print(f"{'  '*indent}[{ord_:2d}] id={nid} {ftype} name='{nname}' classes={classes} sdata={sdata}")
            print_tree(nid, indent+1)
    print_tree(0)
