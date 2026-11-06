import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree
from check_deep_sorting import root

aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"
raw = unpack_unityfs_bundle(aa_dir / "ui-tablefactories_assets_all.bundle")
data_offset = struct.unpack_from(">Q", raw, 32)[0]
pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
trees = []
for ti in range(type_count):
    class_id = struct.unpack_from("<i", raw, pos)[0]
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
    _, nodes = trees[tid]
    try:
        _, val = walk_tree(nodes, raw, abs_off, 0)
    except Exception:
        continue
    if isinstance(val, dict) and "m_rowData" in val:
        mname = val.get("common_427", "")
        if any(w in mname.lower() for w in ("scout", "shortlist", "target", "personsearch", "recruitment")):
            params = val.get("m_parameters", [])
            print(f"\nObj {i:3d} (pid={pid}): {mname} | params={[p.get('name')+':'+hex(p.get('m_serialisedType',0)) for p in params]} | rows={len(val['m_rowData'])}")
            for rd in val["m_rowData"][:12]:
                vbs = [(vb.get("from"), vb.get("to")) for vb in rd.get("m_valueBindings", [])]
                print(f"  row {rd.get('m_id')!r}: sort={rd.get('m_sortBinding',{}).get('m_path')!r}, plugin={rd.get('m_sortBindingPlugin')}, asc={rd.get('m_sortAscending')}, vbs={vbs[:2]}")
