import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_deep_sorting import dump_func_details, pe, va_to_off, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end

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

raw_r, trees_r, objs_r, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
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

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname == "Header":
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"\n=== [{iname}] {tname} (type {ti}) methods ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
                    if rva:
                        dump_func_details(f"Header.{mname}", rva)
