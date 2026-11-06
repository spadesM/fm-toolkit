import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import (
    meta, types_off, types_sz, fields_off, get_mstr, dump_func_details, rva_to_method_name
)
from annotate_sorting_usym import dump_annotated

# 1. Print all fields of VirtualisedList, StreamedListView, StreamedTable
num_types = types_sz // 88
for ti in range(num_types):
    toff = types_off + ti * 88
    tu = struct.unpack_from("<22I", meta, toff)
    tname = get_mstr(tu[0])
    if tname in ("VirtualisedList", "StreamedListView", "StreamedTable"):
        print(f"=== Fields of {tname} (type_idx={ti}) ===")
        first_field = tu[8]
        field_count = tu[17] & 0xFFFF
        for fi in range(first_field, first_field + field_count):
            foff = fields_off + fi * 12
            fname_idx, ftype_idx, ftoken = struct.unpack_from("<3I", meta, foff)
            print(f"  [{fi - first_field:2d}] {get_mstr(fname_idx)}")

print("\n" + "="*80 + "\n")
for name, rva in [
    ("0x00abdcc0 (called by SetSortingBinding)", 0x00abdcc0),
    ("StreamedListView.BeginStateChange", 0x015a47a0),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedTable.EntryForColumn", 0x015e9450),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
    ("StreamedTable.UpdatePersistedColumnSortingData", 0x015f1290),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
