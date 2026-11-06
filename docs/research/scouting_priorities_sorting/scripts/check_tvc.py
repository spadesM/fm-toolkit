import struct, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
tv_raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tableviews_assets_all.bundle")

pos = 48
end = tv_raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", tv_raw, pos)[0]
pos += 4
trees = []
for ti in range(2):
    class_id = struct.unpack_from("<i", tv_raw, pos)[0]
    is_stripped = tv_raw[pos + 4]
    script_type_index = struct.unpack_from("<h", tv_raw, pos + 5)[0]
    pos += 7
    if class_id == 114 or script_type_index >= 0:
        pos += 16
    pos += 16
    nn, ssz = struct.unpack_from("<II", tv_raw, pos)
    pos += 8
    nodes_off = pos
    pos += nn * 32
    str_buf = tv_raw[pos : pos + ssz]
    pos += ssz
    def get_tstr(off, sb=str_buf):
        if off & 0x80000000:
            return f"common_{off & 0x7FFFFFFF}"
        e = sb.find(b"\x00", off)
        return sb[off:e].decode("ascii", errors="replace")
    nodes = []
    for i in range(nn):
        ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", tv_raw, nodes_off + i * 32)
        nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))
    dep_cnt = struct.unpack_from("<i", tv_raw, pos)[0]
    pos += 4 + dep_cnt * 4
    trees.append(nodes)

def walk_tree(nodes, data, pos, node_idx=0):
    lvl, tflags, tname, nname, bsz, mflag = nodes[node_idx]
    children = []
    i = node_idx + 1
    while i < len(nodes) and nodes[i][0] > lvl:
        if nodes[i][0] == lvl + 1:
            children.append(i)
        i += 1
    if tname == "common_840":
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
            pos, ev = walk_tree(nodes, data, pos, elem_node)
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
            if tname == "common_161":
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
        if len(children) == 1 and nodes[children[0]][3] == "common_49":
            pos, arr = walk_tree(nodes, data, pos, children[0])
            if mflag & 0x4000:
                pos = (pos + 3) & ~3
            return pos, arr
        obj = {}
        for c in children:
            c_name = nodes[c][3]
            pos, cv = walk_tree(nodes, data, pos, c)
            obj[c_name] = cv
        if mflag & 0x4000:
            pos = (pos + 3) & ~3
        return pos, obj

tvc_nodes = trees[1]
for name, off in [("ScoutPrioritiesTableViewCollection", 264092), ("ScoutPrioritiesTableViewCollection-Small", 440780)]:
    _, obj = walk_tree(tvc_nodes, tv_raw, off - 28)
    print(f"=== {name} ===")
    for k, v in obj.items():
        if k == "m_tableViewSettings":
            print(f"  m_tableViewSettings ({len(v)} views):")
            for vi, view in enumerate(v):
                tv = view.get("m_tableView", view)
                print(f"    View {vi}: {list(view.keys())}")
                if isinstance(tv, dict) and "m_tableConfig" in tv:
                    for col in tv["m_tableConfig"]:
                        md = col["m_columnMetadata"]
                        print(f"      col={col['m_columnID']!r:25s} req={md['m_required']} sortingDisabled={md['m_sortingDisabled']} width={md['m_widthOverride']}")
                else:
                    print(f"      {view}")
        else:
            print(f"  {k}: {v}")
