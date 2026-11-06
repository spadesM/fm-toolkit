import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\streamed_table_and_views_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Inspect ui-tableviews_assets_all.bundle ===")
raw_v, trees_v, objs_v, ref_trees_v = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_v:
    if tid in trees_v:
        _, nodes = trees_v[tid]
        chunk = raw_v[abs_off : abs_off + bsize]
        try:
            _, props = walk_tree(nodes, chunk, 0, 0)
            name = props.get("m_Name", props.get("common_427", ""))
            if any(k in name for k in ("ScoutPriorities", "Shortlist", "PlayerDatabase", "PlayerSearch", "SpecificallyScouted")):
                print(f"\nView Obj {oi:3d} (pid={pid}, name={name!r}, size={bsize}):")
                for k, v in props.items():
                    if k != "m_Script":
                        print(f"  {k}: {v}")
        except Exception as e:
            pass

print("\n=== 2. List ALL methods of StreamedTable, StreamedTableHeaderCell, TableViewSpec, TableFactory ===")
hdr = struct.unpack_from("<80I", meta, 0)
types_sz = hdr[41]
num_types = types_sz // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if any(k in tname for k in ("StreamedTable", "TableFactory", "TableView", "HeaderCell")):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (methods={m_cnt})")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            found_rvas = [r for r, nms in rva_to_method_name.items() if f"{tname}.{mname}" in nms]
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in found_rvas]}")

out_file.close()
