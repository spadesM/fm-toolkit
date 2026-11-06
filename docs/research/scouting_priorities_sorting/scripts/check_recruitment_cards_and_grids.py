import sys, struct, re
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree, inspect_bundle

# Check externals of ui-recruitment_assets_all.bundle
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

# Find external files of ui-recruitment_assets_all.bundle
data_offset = struct.unpack_from(">Q", raw, 32)[0]
pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]; pos += 4
for _ in range(type_count):
    cid = struct.unpack_from("<i", raw, pos)[0]
    sti = struct.unpack_from("<h", raw, pos + 5)[0]
    pos += 7 + (16 if (cid == 114 or sti >= 0) else 0) + 16
    nn, ssz = struct.unpack_from("<II", raw, pos); pos += 8 + nn * 32 + ssz
    dc = struct.unpack_from("<i", raw, pos)[0]; pos += 4 + dc * 4
obj_count = struct.unpack_from("<i", raw, pos)[0]; pos += 4
for _ in range(obj_count):
    pos = (pos + 3) & ~3; pos += 24
sc = struct.unpack_from("<i", raw, pos)[0]; pos += 4
for _ in range(sc):
    pos += 4; pos = (pos + 3) & ~3; pos += 8
ec = struct.unpack_from("<i", raw, pos)[0]; pos += 4
for idx in range(ec):
    e = raw.find(b"\x00", pos); pos = e + 1 + 16 + 4
    e2 = raw.find(b"\x00", pos)
    print(f"Ext fileID={idx+1}: {raw[pos:e2].decode('utf-8', errors='replace')}")
    pos = e2 + 1

# Also check ALL StreamedTable instances across ALL objects in ui-recruitment_assets_all.bundle!
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]
print("\n=== ALL StreamedTables in ui-recruitment_assets_all.bundle ===")
for i, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    if b"StreamedTable/UxmlSerializedData" in chunk:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        for m in re.finditer(rb"StreamedTable/UxmlSerializedData", chunk):
            p = m.start() + 64
            val = {}
            for c in top_children:
                cname = st_nodes[c][3]
                if cname == "references":
                    break
                p, cv = walk_tree(st_nodes, chunk, p, c)
                val[cname] = cv
            bpath = val.get("Binding", {}).get("m_direct", {}).get("Path", {}).get("m_path", "")
            bfunc = val.get("Binding", {}).get("m_visualFunction", {}).get("m_target", {}).get("m_AssetGUID", "")
            init_g = val.get("InitFunction", {}).get("m_target", {}).get("m_AssetGUID", "")
            fac_g = val.get("FactoryAsset", {}).get("m_AssetGUID", "")
            dis_s = val.get("DisableSorting", 0)
            reord = val.get("Reorderable", 0)
            print(f"  Obj {i:3d} ({name}): bind='{bpath}' (vf={bfunc[:8]}) init={init_g[:8]} fac={fac_g[:8]} disSort={dis_s} reord={reord}")
