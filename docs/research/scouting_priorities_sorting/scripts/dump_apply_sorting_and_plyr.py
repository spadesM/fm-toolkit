import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\apply_sorting_and_plyr_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

print("=== 1. Find Reference class with ID 0x706c7972 ('plyr') ===")
idx = 0
while True:
    idx = pe.find(b"\xb8\x72\x79\x6c\x70\xc3", idx)
    if idx == -1:
        break
    va = off_to_va(idx)
    if va:
        rva = va - image_base
        print(f"Found mov eax, 0x706c7972; ret at RVA={hex(rva)} -> {rva_to_method_name.get(rva)}")
    idx += 1

print("\n=== 2. Dump StreamedListView sorting & state resolution methods ===")
slv_dumps = [
    ("StreamedListView.SetSortingBinding(1)", 0x15a9a80),
    ("StreamedListView.SetSortingBinding(2)", 0x15a9ae0),
    ("StreamedListView.SetSorting_internal_0xabdcc0", 0x00abdcc0),
    ("StreamedListView.UpdateSortingBinding", 0x15ab800),
    ("StreamedListView.HasSorting", 0x15a5f20),
    ("StreamedListView.ApplySorting", 0x15a4260),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x15aa320),
    ("StreamedListView.BindSortPathNextDepth", 0x15a4850),
    ("StreamedListView.OnSortingDataChanged", 0x15a7ff0),
    ("StreamedListView.ProcessSortingDataChanged", 0x15a8cb0),
    ("StreamedListView.PostSortingDataChanged", 0x15a8610),
    ("StreamedListView.SetNoSorting", 0x15a99d0),
    ("StreamedListView.ClearSortingState", 0x15a5180),
    ("StreamedListView.OnSortBindingChanged", 0x15a7ca0),
    ("StreamedListView.OnResetSortingEvent", 0x15a7870),
    ("StreamedListView.ResolveStateChanges", 0x15a9620),
    ("StreamedListView.StateChanged", 0x15a9c80),
    ("StreamedListView.UpdateEnabledState", 0x15aab80),
    ("StreamedListView.Rebuild", 0x15a8eb0),
    ("StreamedListView.Refresh", 0x15a9390),
    ("StreamedListView.CanBuild", 0x15a50b0),
    ("StreamedTable.CanBuild", 0x15e7580),
    ("StreamedTable.TrySetColumnsAndSort", 0x15f0040),
]

for label, rva in slv_dumps:
    sz = min(rva_to_end.get(rva, rva + 1024) - rva, 2000)
    dump_func_details(label, rva, sz)

out_file.close()
