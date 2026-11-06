import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\dump_nth_prop_and_sortdata.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

dumps = [
    ("Bindings.GetNthProperty", 0x014c1450),
    ("Bindings.GetProperties", 0x014c1a60),
    ("SortData.HasReceived", 0x015a4040),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.SetSorting(1)", 0x015efc40),
    ("StreamedTable.SetSorting(2)", 0x015efce0),
    ("StreamedTable.EntryForColumn", 0x015e9450),
    ("StreamedTable.InitialiseColumns", 0x015ea870),
    ("StreamedTable.CreateColumns", 0x015e83b0),
    ("StreamedTable.OnViewSet", 0x015ee7a0),
    ("StreamedTable.<OnViewSet>b__297_0", 0x015f0800),
    ("StreamedTable.BindHeaders", 0x015e6ca0),
    ("StreamedTable.BindToDataInternal", 0x015e6d70),
]

for label, rva in dumps:
    sz = min(rva_to_end.get(rva, rva + 1024) - rva, 2000)
    dump_func_details(label, rva, sz)

out_file.close()
