import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
from check_deep_sorting import dump_func_details

dump_func_details("SetSortingBinding<T> (0x00abdcc0)", 0x00abdcc0, 0x300)

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]

print("\n=== All StreamedTables in ui-recruitment_assets_all.bundle ===")
for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    if b"StreamedTable/UxmlSerializedData" not in chunk:
        continue
    ln = struct.unpack_from("<I", chunk, 28)[0]
    vta_name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else f"Obj_{oi}"
    pos = 0
    while True:
        idx = chunk.find(b"StreamedTable/UxmlSerializedData", pos)
        if idx < 0:
            break
        data_pos = idx + 0x40
        p = data_pos
        d = {}
        try:
            for i, n in enumerate(st_nodes):
                if n[0] == 1:
                    fn = n[3]
                    if fn == "references":
                        break
                    p, fv = walk_tree(st_nodes, chunk, p, i)
                    d[fn] = fv
            tc = d.get("TableConfig", {}).get("m_AssetGUID", "")
            tvb = d.get("TableViewBinding", {}).get("m_path", "")
            vdn = d.get("ViewDropdownName", "")
            sc = d.get("SortedColumn", "")
            sa = d.get("SortAscending", 0)
            ds = d.get("DisableSorting", 0)
            ro = d.get("Reorderable", 0)
            bd = d.get("Binding", {}).get("m_path", "")
            sb = d.get("SortBinding", {}).get("m_path", "")
            fa = d.get("FactoryAsset", {}).get("m_AssetGUID", "")
            init_guid = d.get("InitFunction", {}).get("m_target", {}).get("m_AssetGUID", "")
            print(f"  Obj {oi:3d} ({vta_name:42s}): DisSort={ds} Reord={ro} SortAsc={sa} SortedCol={sc!r:15s} Bind={bd!r:48s} SortBind={sb!r:20s} TC={tc[:8]:8s} TVB={tvb!r:20s} VDN={vdn!r:15s} Fac={fa[:8]} Init={init_guid[:8]}")
        except Exception as e:
            print(f"  Obj {oi:3d} ({vta_name}): err {e}")
        pos = idx + 32
