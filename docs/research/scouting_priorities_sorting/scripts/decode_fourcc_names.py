import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, hdr, va_to_off, off_to_va, image_base, root
)
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree

# 1. Print remaining TypeTree nodes of VisualTreeAsset (120..321) and parse m_VisualElementAssets of Obj 229, 263, 177
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

class_id, vta_nodes = trees[objs[229][4]]
print("=== VisualTreeAsset level-1 children ===")
for idx, (lvl, tflags, tname, nname, bsz, mflag) in enumerate(vta_nodes):
    if lvl <= 2:
        print(f"  {idx:3d}: {'  '*lvl}{tname} {nname} (tflags={tflags}, bsz={bsz}, mflag=0x{mflag:x})")

def parse_vta_up_to_refs(obj_idx):
    oi, pid, abs_off, bsize, tid = objs[obj_idx]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {}
    for c in top_children:
        cname = nodes[c][3]
        if cname == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[cname] = val
    print(f"\n=== VisualTreeAsset Obj {obj_idx} ({res.get('common_427')}) ===")
    for vea in res.get("m_VisualElementAssets", []):
        print(f"  VE id={vea['m_Id']} parent={vea['m_ParentId']} order={vea['m_OrderInDocument']} type={vea['m_FullTypeName']} name={vea['common_427']!r} pick={vea['m_PickingMode']} classes={vea['m_Classes']} props={vea['m_Properties']} rid={vea['m_SerializedData']['rid']}")
    for ta in res.get("m_TemplateAssets", []):
        print(f"  TA id={ta['m_Id']} parent={ta['m_ParentId']} order={ta['m_OrderInDocument']} template={ta['m_TemplateAlias']!r} props={ta['m_Properties']} rid={ta['m_SerializedData']['rid']}")

for target_oi in (177, 229, 263, 360):
    parse_vta_up_to_refs(target_oi)
