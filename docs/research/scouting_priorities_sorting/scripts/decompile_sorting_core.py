import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, types_off, fields_off, get_mstr,
    va_to_off, off_to_va, image_base, rva_to_method_name, dump_func_details
)

# 1. Print all fields of StreamedListView (Type 5791) and StreamedTable (Type 5967)
# Wait: how are field offsets stored in Il2CppGlobalMetadata / GameAssembly.dll?
# Let's check check_deep_sorting.py or find field names of Type 5791 and 5967
for tid in (5791, 5967):
    t_entry = types_off + tid * 88
    name_idx, ns_idx = struct.unpack_from("<II", meta, t_entry)
    field_start, method_start = struct.unpack_from("<ii", meta, t_entry + 32)
    field_count, method_count = struct.unpack_from("<HH", meta, t_entry + 72)
    print(f"\n=== Type {tid}: {get_mstr(ns_idx)}.{get_mstr(name_idx)} (fields={field_count}) ===")
    for fi in range(field_start, field_start + field_count):
        f_name_idx, f_type_idx, f_token = struct.unpack_from("<IiI", meta, fields_off + fi * 12)
        print(f"  field[{fi - field_start:2d}]: {get_mstr(f_name_idx)}")

dump_func_details("StreamedListView.ApplySorting", 0x015a4260, 0x600)
dump_func_details("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x350)
dump_func_details("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x320)
dump_func_details("Bindings.SetAlias", 0x014c3050, 0x350)
dump_func_details("Bindings.Create", 0x014bf980, 0x200)
dump_func_details("StreamedTable.OnBindItem", 0x015eb760, 0x350)
dump_func_details("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580, 0x350)
