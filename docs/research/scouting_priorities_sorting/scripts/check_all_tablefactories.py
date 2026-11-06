import struct, sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_refs_and_grid import resolve_fm_install_dir, unpack_unityfs_bundle, walk_tree

root = resolve_fm_install_dir()
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tablefactories_assets_all.bundle")
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
        nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))
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

for i, pid, abs_off, bsize, tid in objs:
    class_id, nodes = trees[tid]
    if class_id == 114:
        try:
            _, data = walk_tree(nodes, raw, abs_off, 0)
            if isinstance(data, dict) and "m_rowData" in data:
                name = data.get("common_427", "")
                cols = data.get("m_rowData", [])
                base_f = data.get("m_baseFactories", [])
                multi_cols = []
                single_cols = []
                plugin_cols = []
                for c in cols:
                    cid = c.get("m_id", "")
                    sb = c.get("m_sortBinding", {}).get("m_path", "")
                    sp = c.get("m_sortBindingPlugin", 0)
                    if sb:
                        stripped = sb[8:] if sb.startswith("binding.") else sb
                        if "." in stripped:
                            multi_cols.append((cid, sb, sp))
                        else:
                            single_cols.append((cid, sb, sp))
                    elif sp:
                        plugin_cols.append((cid, sb, sp))
                if multi_cols:
                    print(f"Obj {i:3d} {name}: base={len(base_f)}, total={len(cols)}, single={len(single_cols)}, multi={len(multi_cols)}, plugin={len(plugin_cols)} -> sample={multi_cols[:4]}")
        except Exception:
            pass
