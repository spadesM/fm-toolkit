import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
tf_raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tablefactories_assets_all.bundle")

pos = 48
end = tf_raw.find(b"\x00", pos)
pos = end + 1 + 5 + 4
pos += 7 + 16 + 16
nn, ssz = struct.unpack_from("<II", tf_raw, pos)
pos += 8
nodes_off = pos
pos += nn * 32
str_buf = tf_raw[pos : pos + ssz]
def get_tstr(off):
    if off & 0x80000000:
        return f"common_{off & 0x7FFFFFFF}"
    e = str_buf.find(b"\x00", off)
    return str_buf[off:e].decode("ascii", errors="replace")
tf_nodes = []
for i in range(nn):
    ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", tf_raw, nodes_off + i * 32)
    tf_nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))

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

for name, off in [
    ("SpecificallyScoutedPersonTableFactory", 461792),
    ("SpecificallyScoutedTeamTableFactory", 732480),
    ("NotInterestedPlayersTableFactory", 659792),
    ("RecruitmentFeedbackTableFactory", 685872),
    ("TeamReportPrioritiesTableFactory", 691840),
    ("ScoutingFocusTableFactory", 561696),
    ("PlayerTableFactory", 198000),
]:
    _, obj = walk_tree(tf_nodes, tf_raw, off)
    print(f"\n=== {name} (rows={len(obj['m_rowData'])}) ===")
    print(f"  params: {[(p['name'], p['m_serialisedType']) for p in obj['m_parameters']]}")
    for rd in obj["m_rowData"][:15]:
        print(f"  id={rd['m_id']!r:28s} sortBinding={rd['m_sortBinding']['m_path']!r:45s} plugin={rd['m_sortBindingPlugin']:6d} asc={rd['m_sortAscending']}")
