import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree
from check_deep_sorting import root

aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

def parse_bundle(bundle_name):
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
    return raw, trees, objs

def find_objs(bundle_name, filter_names):
    raw, trees, objs = parse_bundle(bundle_name)
    out = {}
    for i, pid, abs_off, bsize, tid in objs:
        _, nodes = trees[tid]
        try:
            _, val = walk_tree(nodes, raw, abs_off, 0)
        except Exception:
            continue
        if isinstance(val, dict):
            mname = val.get("common_427", "") or val.get("m_Name", "")
            if any(fn.lower() in str(mname).lower() for fn in filter_names):
                out[mname] = (i, pid, val)
    return out

factories = find_objs("ui-tablefactories_assets_all.bundle", [
    "SpecificallyScoutedPerson", "ShortlistPerson", "TransferTarget", "TeamReportPriorit"
])
print("=== TABLE FACTORIES ===")
for fname, (oi, pid, val) in factories.items():
    print(f"\nFactory: {fname} (Obj {oi}, path_id={pid})")
    for k, v in val.items():
        if k not in ("m_rowData", "m_Script", "common_427"):
            print(f"  {k}: {v}")
    row_data = val.get("m_rowData", [])
    print(f"  m_rowData ({len(row_data)} entries):")
    for rd in row_data:
        print(f"    id={rd.get('m_id')!r}: sortBinding={rd.get('m_sortBinding')!r}, sortPlugin={rd.get('m_sortBindingPlugin')}, sortAsc={rd.get('m_sortAscending')}, headerLabelBinding={rd.get('m_headerLabelBinding')!r}")

views = find_objs("ui-tableviews_assets_all.bundle", [
    "ScoutPriorities", "ShortlistOverview", "TransferTargets"
])
print("\n=== TABLE VIEWS ===")
for vname, (oi, pid, val) in views.items():
    print(f"\nView: {vname} (Obj {oi}, path_id={pid})")
    for k, v in val.items():
        if k not in ("m_tableConfig", "m_Script", "common_427"):
            print(f"  {k}: {v}")
    tcfg = val.get("m_tableConfig", [])
    print(f"  m_tableConfig ({len(tcfg)} cols):")
    for col in tcfg:
        print(f"    col={col.get('m_columnID')!r}: meta={col.get('m_columnMetadata')}")
