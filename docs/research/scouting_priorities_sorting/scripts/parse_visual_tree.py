import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")
data_offset = struct.unpack_from(">Q", raw, 32)[0]
pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
trees = []
for ti in range(type_count):
    class_id = struct.unpack_from("<i", raw, pos)[0]
    is_stripped = raw[pos + 4]
    script_type_index = struct.unpack_from("<h", raw, pos + 5)[0]
    pos += 7
    if class_id == 114 or script_type_index >= 0:
        pos += 16
    pos += 16
    nn, ssz = struct.unpack_from("<II", raw, pos)
    pos += 8
    nodes_off = pos
    pos += nn * 32
    str_buf = raw[pos : pos + ssz]
    pos += ssz
    def get_tstr(off, sb=str_buf):
        if off & 0x80000000:
            return f"common_{off & 0x7FFFFFFF}"
        e = sb.find(b"\x00", off)
        return sb[off:e].decode("ascii", errors="replace")
    nodes = []
    for i in range(nn):
        ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, nodes_off + i * 32)
        nodes.append((i, lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))
    dep_cnt = struct.unpack_from("<i", raw, pos)[0]
    pos += 4 + dep_cnt * 4
    trees.append((class_id, nodes))

obj_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
objs = []
for i in range(obj_count):
    pos = (pos + 3) & ~3
    pid, bstart, bsize, tid = struct.unpack_from("<qQII", raw, pos)
    pos += 24
    objs.append((i, pid, data_offset + bstart, bsize, tid))

oi, pid, abs_off, bsize, tid = objs[229]
class_id, nodes = trees[tid]
print(f"Obj 229 tid={tid} class_id={class_id} nodes={len(nodes)}")
for idx, lvl, tflags, tname, nname, bsz, mflag in nodes[:120]:
    print(f"  {idx:3d}: {'  '*lvl}{tname} {nname} (tflags={tflags}, bsz={bsz}, mflag=0x{mflag:x})")
