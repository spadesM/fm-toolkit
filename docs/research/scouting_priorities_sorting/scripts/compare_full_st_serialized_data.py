import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree
from check_deep_sorting import root

aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

def parse_bundle_with_reftypes(bundle_name):
    raw = unpack_unityfs_bundle(aa_dir / bundle_name)
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

    script_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    for _ in range(script_count):
        pos += 4
        pos = (pos + 3) & ~3
        pos += 8

    ext_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    for _ in range(ext_count):
        e = raw.find(b"\x00", pos)
        pos = e + 1 + 16 + 4
        e2 = raw.find(b"\x00", pos)
        pos = e2 + 1

    ref_type_count = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    ref_trees = {}
    for rti in range(ref_type_count):
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
        def get_rtstr(off, sb=str_buf):
            if off & 0x80000000:
                return f"common_{off & 0x7FFFFFFF}"
            e = sb.find(b"\x00", off)
            return sb[off:e].decode("ascii", errors="replace")
        nodes = []
        for i in range(nn):
            ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, nodes_off + i * 32)
            nodes.append((lvl, tflags, get_rtstr(t_off), get_rtstr(n_off), bsz, mflag))
        e1 = raw.find(b"\x00", pos)
        cls_name = raw[pos:e1].decode("utf-8", errors="replace")
        pos = e1 + 1
        e2 = raw.find(b"\x00", pos)
        ns_name = raw[pos:e2].decode("utf-8", errors="replace")
        pos = e2 + 1
        e3 = raw.find(b"\x00", pos)
        asm_name = raw[pos:e3].decode("utf-8", errors="replace")
        pos = e3 + 1
        ref_trees[cls_name] = nodes
    return raw, trees, objs, ref_trees

if __name__ == "__main__":
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
    st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
    print(f"st_nodes count = {len(st_nodes)}, root = {st_nodes[0]}")
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

    for oi in (229, 263, 111, 103):
        _, pid, abs_off, bsize, tid = objs[oi]
        chunk = raw[abs_off : abs_off + bsize]
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        pat = b"StreamedTable/UxmlSerializedData"
        idx = chunk.find(pat)
        if idx != -1:
            p = idx + 64
            print(f"\n==================== Obj {oi} ({name}) dstart={p} ====================")
            for c in top_children:
                cname = st_nodes[c][3]
                try:
                    p_next, val = walk_tree(st_nodes, chunk, p, c)
                    if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                        print(f"  +0x{p - (idx+64):03x} {cname}: {val}")
                    p = p_next
                except Exception as e:
                    print(f"  ERROR at {cname} (+0x{p - (idx+64):03x}): {e}")
                    break
