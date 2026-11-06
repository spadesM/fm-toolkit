import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree

def load_bundle(bundle_name):
    raw = unpack_unityfs_bundle(root / f"fm_Data/StreamingAssets/aa/StandaloneWindows64/{bundle_name}")
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
    return raw, trees, objs

def parse_obj(raw, trees, objs, obj_idx):
    oi, pid, abs_off, bsize, tid = objs[obj_idx]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {"_pid": pid, "_bsize": bsize}
    for c in top_children:
        cname = nodes[c][3]
        if cname == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[cname] = val
    return res

print("=== 1. Check ui-visualfunctions_assets_all.bundle ===")
raw_vf, trees_vf, objs_vf = load_bundle("ui-visualfunctions_assets_all.bundle")
for i in range(len(objs_vf)):
    try:
        d = parse_obj(raw_vf, trees_vf, objs_vf, i)
        name = d.get("common_427", "")
        if "StreamedTable" in str(name):
            print(f"\nVF Obj[{i}] ({name}):")
            for k, v in d.items():
                print(f"  {k}: {v!r}")
    except Exception as e:
        pass

print("\n=== 2. Check ui-tablefactories_assets_all.bundle ===")
raw_tf, trees_tf, objs_tf = load_bundle("ui-tablefactories_assets_all.bundle")
for i in range(len(objs_tf)):
    try:
        d = parse_obj(raw_tf, trees_tf, objs_tf, i)
        name = d.get("common_427", "")
        if any(w in str(name) for w in ("SpecificallyScouted", "Shortlist", "PersonSearch", "ScoutPriorities", "TransferTargets")):
            print(f"\nTF Obj[{i}] ({name}, pid={d['_pid']}):")
            for k, v in d.items():
                if k == "m_configurations":
                    print(f"  m_configurations ({len(v)} cols):")
                    for col in v[:15]:
                        print(f"    col={col.get('m_columnID')!r} sort={col.get('m_sortBinding')!r} disableSort={col.get('m_disableSorting')!r} keys={[ck for ck, cv in col.items() if cv not in (0, '', [], {}, {'m_path': ''})]}")
                else:
                    print(f"  {k}: {v!r}")
    except Exception as e:
        pass
