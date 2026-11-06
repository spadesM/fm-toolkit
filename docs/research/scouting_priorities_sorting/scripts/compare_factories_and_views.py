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
    return raw, trees, objs

print("=== 1. Inspect SpecificallyScoutedPersonTableFactory vs SpecificallyScoutedTeamTableFactory vs PersonTableFactory ===")
raw_tf, trees_tf, objs_tf = parse_bundle_fast("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_tf:
    chunk = raw_tf[abs_off : abs_off + bsize]
    class_id, nodes = trees_tf[tid]
    if class_id == 114:
        _, val = walk_tree(nodes, chunk, 0, 0)
        name = next((v for v in val.values() if isinstance(v, str) and v), "")
        if any(k in name for k in ["Scout", "PersonTableFactory", "Shortlist", "Recommend"]):
            print(f"\nTableFactory Obj {oi} ({name}, PathID={pid}):")
            for k, v in val.items():
                if not k.startswith("common_") and k != "m_columnData":
                    print(f"  {k}: {v}")
            cols = val.get("m_columnData", [])
            print(f"  m_columnData ({len(cols)} columns):")
            for c in cols[:25]:
                cid = c.get("m_columnID")
                sb = c.get("m_sortBinding", {}).get("m_path", "")
                sbp = c.get("m_sortBindingPlugin")
                vb = [(b.get("m_from", {}).get("m_path", ""), b.get("m_to", {}).get("m_path", "")) for b in c.get("m_valueBindings", [])]
                hca = c.get("m_headerCellAsset", {}).get("m_AssetGUID", "")
                print(f"    col={cid!r:25s} sortBinding={sb!r:55s} plugin={sbp} headerAsset={hca!r} valBindings={vb}")

print("\n=== 2. Inspect TableViews in ui-tableviews_assets_all.bundle ===")
raw_tv, trees_tv, objs_tv = parse_bundle_fast("ui-tableviews_assets_all.bundle")
pid_to_tv = {}
for oi, pid, abs_off, bsize, tid in objs_tv:
    chunk = raw_tv[abs_off : abs_off + bsize]
    class_id, nodes = trees_tv[tid]
    if class_id == 114:
        _, val = walk_tree(nodes, chunk, 0, 0)
        pid_to_tv[pid] = (oi, val)

for pid, (oi, val) in sorted(pid_to_tv.items(), key=lambda x: x[1][0]):
    name = next((v for v in val.values() if isinstance(v, str) and v), "")
    if any(k in name for k in ["ScoutPriorities", "ScoutTeam", "Recommendations", "Shortlist", "Scouted"]):
        print(f"\nTableView/Collection Obj {oi} ({name}, PathID={pid}):")
        for k, v in val.items():
            if not k.startswith("common_"):
                print(f"  {k}: {v}")
