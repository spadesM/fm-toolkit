import struct, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle
from check_refs_and_grid import walk_tree

aa_dir = resolve_fm_install_dir() / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

def parse_bundle_fast(bundle_name):
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
    raw, trees, objs, ref_trees = parse_bundle_fast("ui-recruitment_assets_all.bundle")
    st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

    print("=== All StreamedTable objects in ui-recruitment_assets_all.bundle ===")
for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    if idx != -1:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        # Find exact start of StreamedTable/UxmlSerializedData payload:
        # InManagedRef: 8-byte rid, then class string, namespace string ("SI.Bindable"), asm string ("SI.Bindable")
        asm_idx = chunk.find(b"SI.Bindable", idx + 32)
        asm_idx2 = chunk.find(b"SI.Bindable", asm_idx + 11)
        p = ((asm_idx2 + 11 + 3) & ~3)
        props = {}
        try:
            for c in top_children:
                cname = st_nodes[c][3]
                p, val = walk_tree(st_nodes, chunk, p, c)
                if cname in ("Binding", "SelectedItemsBinding", "InitFunction", "FactoryAsset", "Reorderable", "DisableSorting", "DragCellID", "DragEvents", "SortingBinding", "TableViews"):
                    props[cname] = val
        except Exception as e:
            props["ERROR"] = str(e)
        print(f"\nObj {oi:3d} ({name}, PathID={pid}):")
        for k, v in props.items():
            if k == "InitFunction" and isinstance(v, dict):
                ab = bytes(v.get("m_inputs", {}).get("m_variable", {}).get("m_argumentBytes", []))
                v = {"target": v.get("m_target", {}).get("m_AssetGUID"), "args_ascii": ab.decode("ascii", errors="replace")}
            print(f"  {k}: {v}")
