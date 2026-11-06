import sys
import struct
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

sys.stdout.reconfigure(encoding="utf-8")

root = resolve_fm_install_dir()
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")

hdr_off = 133841
nn, ssz = struct.unpack_from("<II", raw, hdr_off)
nodes_off = hdr_off + 8
str_off = nodes_off + nn * 32
str_buf = raw[str_off : str_off + ssz]

def get_tstr(off):
    if off & 0x80000000:
        return f"common_{off & 0x7FFFFFFF}"
    end = str_buf.find(b"\x00", off)
    return str_buf[off:end].decode("ascii", errors="replace")

nodes = []
for i in range(nn):
    ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, nodes_off + i * 32)
    nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))

def walk_node(data, pos, node_idx):
    lvl, tflags, tname, nname, bsz, mflag = nodes[node_idx]
    children = []
    i = node_idx + 1
    while i < len(nodes) and nodes[i][0] > lvl:
        if nodes[i][0] == lvl + 1:
            children.append(i)
        i += 1

    start_pos = pos
    val = None
    if tname == "common_840":
        slen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        sval = data[pos : pos + slen].decode("utf-8", errors="replace")
        pos += slen
        pos = (pos + 3) & ~3
        val = repr(sval)
    elif tflags & 1:
        alen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        elem_idx = children[1]
        if nodes[elem_idx][4] == 1 and not (nodes[elem_idx][0] + 1 < len(nodes) and nodes[elem_idx + 1][0] > nodes[elem_idx][0]):
            val = f"bytes[{alen}]={data[pos:pos+alen].hex()}"
            pos += alen
        else:
            arr = []
            for _ in range(alen):
                pos, eval_ = walk_node(data, pos, elem_idx)
                arr.append(eval_)
            val = f"Array[{alen}]={arr}"
    elif bsz > 0 and not children:
        raw_bytes = data[pos : pos + bsz]
        if bsz == 1:
            val = raw_bytes[0]
        elif bsz == 4:
            if tname == "common_161":
                val = round(struct.unpack_from("<f", data, pos)[0], 3)
            else:
                val = struct.unpack_from("<i", data, pos)[0]
        elif bsz == 8:
            val = struct.unpack_from("<q", data, pos)[0]
        else:
            val = raw_bytes.hex()
        pos += bsz
    else:
        sub_vals = {}
        for c_idx in children:
            pos, cval = walk_node(data, pos, c_idx)
            sub_vals[nodes[c_idx][3]] = cval
        val = sub_vals

    if mflag & 0x4000:
        pos = (pos + 3) & ~3

    if lvl == 1:
        print(f"  [0x{start_pos:04x}..0x{pos:04x}] {nname:<42} = {val}")
    return pos, val

for label, st_pos in [
    ("ScoutPrioritiesBlock", 2358236),
    ("ScoutPrioritiesBlock-Small", 2616996),
    ("ShortlistMainBlock", 1412100),
    ("TeamPriorities", 3323400),
]:
    print(f"\n==================== {label} (st_pos={st_pos}) ====================")
    sub = raw[st_pos : st_pos + 1600]
    walk_node(sub, 0x40, 0)
