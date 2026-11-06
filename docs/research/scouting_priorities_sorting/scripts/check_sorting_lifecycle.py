import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, pe, va_to_off, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end

for name, rva in [
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.OnResetSortingEvent", 0x015a7870),
    ("StreamedListView.SetNoSorting", 0x015a99d0),
    ("StreamedTable.SetNoSorting", 0x015ef750),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
    ("StreamedTable.CreateColumns", 0x015e83b0),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
]:
    dump_func_details(name, rva)
