import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\investigation_output.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Locate Il2CppMetadataRegistration to get exact fieldOffsets!
# Il2CppMetadataRegistration has:
# int64 genericClassesCount, genericClasses, genericInstsCount, genericInsts, genericMethodTableCount, genericMethodTable,
# int64 typesCount, types, methodSpecsCount, methodSpecs, fieldOffsetsCount, fieldOffsets, typeDefinitionsSizesCount, typeDefinitionsSizes, ...
num_types_defs = struct.unpack_from("<64I", meta, 0)[41] // 88
print(f"Total TypeDefinitions: {num_types_defs}")

field_offsets_va = 0
# Search for struct containing fieldOffsetsCount == num_types_defs and typeDefinitionsSizesCount == num_types_defs
pattern = struct.pack("<Q", num_types_defs)
pos = 0
while True:
    idx = pe.find(pattern, pos)
    if idx < 0:
        break
    # Check if idx + 16 also has num_types_defs (fieldOffsetsCount, fieldOffsets, typeDefinitionsSizesCount, typeDefinitionsSizes)
    if idx + 32 <= len(pe):
        c1, p1, c2, p2 = struct.unpack_from("<4Q", pe, idx)
        if c1 == num_types_defs and c2 == num_types_defs:
            off1 = va_to_off(p1)
            off2 = va_to_off(p2)
            if off1 > 0 and off2 > 0:
                field_offsets_va = p1
                print(f"Found fieldOffsets table at VA=0x{p1:016x} (file_off=0x{off1:x})")
                break
    pos = idx + 8

field_offsets_table_off = va_to_off(field_offsets_va) if field_offsets_va else -1

print("\n=== 1. Exact Fields & Offsets in SI.Bindable.dll & FM.UI.dll ===")
target_type_names = {
    "VirtualisedList", "StreamedListView", "StreamedTable",
    "Header", "Column", "ColumnConfig", "RowData", "TableFactory",
    "UxmlSerializedData", "SortOrder", "Entry"
}

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in ("SI.Bindable.dll", "FM.UI.dll"):
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        decl_ti = tu[3]
        parent_name = ""
        if decl_ti >= 0:
            # Wait: tu[3] is declaringTypeIndex (actually typeIndex in Il2CppType table, or let's check!)
            pass
        if tname in target_type_names or any(k in tname for k in ("StreamedTable", "StreamedListView", "VirtualisedList", "TableFactory", "SpecificallyScouted", "ScoutPriorities")):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            foff_arr_off = -1
            if field_offsets_table_off > 0:
                arr_va = struct.unpack_from("<Q", pe, field_offsets_table_off + ti * 8)[0]
                if arr_va > 0:
                    foff_arr_off = va_to_off(arr_va)
            print(f"\n--- [{iname}] Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                fname = get_mstr(fu[0])
                foff_val = struct.unpack_from("<I", pe, foff_arr_off + (fi - f_start) * 4)[0] if foff_arr_off > 0 else -1
                print(f"  Field {fi - f_start:2d} (+0x{foff_val:03x}): {fname}")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - image_base if va else 0
                print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")

print("\n=== 2. TableView Assets in ui-tableviews_assets_all.bundle ===")
raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi in (236, 400, 766, 791, 729):
    _, pid, abs_off, bsize, tid = objs_v[oi]
    _, nodes = trees_v[tid]
    chunk = raw_v[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- TableView Obj {oi} (pid={pid}) ---")
    for k, v in val.items():
        if k != "m_tableConfig":
            print(f"  {k}: {v}")
        else:
            print(f"  m_tableConfig ({len(v)} cols):")
            for col in v:
                print(f"    {col}")

print("\n=== 3. Factory Assets in ui-tablefactories_assets_all.bundle ===")
raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi in (92, 118, 31):
    _, pid, abs_off, bsize, tid = objs_f[oi]
    _, nodes = trees_f[tid]
    chunk = raw_f[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- Factory Obj {oi} (pid={pid}) ---")
    for k, v in val.items():
        if k != "m_rowData":
            print(f"  {k}: {v}")
        else:
            print(f"  m_rowData ({len(v)} cols):")
            for r in v[:40]:
                print(f"    {r}")
            if len(v) > 40:
                print(f"    ... ({len(v) - 40} more rows)")

out_file.flush()
out_file.close()
