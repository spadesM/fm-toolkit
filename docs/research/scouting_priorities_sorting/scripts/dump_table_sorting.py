import struct
from annotate_sorting_usym import dump_annotated, pe, meta, va_to_off, image_base, get_mstr, types_off, hdr
from check_deep_sorting import dump_func_details

targets = [
    ("StreamedListView.ApplySorting", 0x015a4260, 1208),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 785),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 342),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 200),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 509),
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 500),
    ("StreamedTable.SetSorting_2", 0x015efce0, 0x290),
    ("StreamedTable.sub_015eff70", 0x015eff70, 0xd0),
    ("StreamedTable.sub_015f0040", 0x015f0040, 0x200),
    ("StreamedTable.EntryForColumn", 0x015e9450, 0x150),
    ("StreamedTable.GetBindingKind", 0x015e9cf0, 0x250),
    ("StreamedTable.GetIdentifiers", 0x015ea360, 0x250),
    ("StreamedTable.UpdateSortColumn", 0x015f1380, 0x250),
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80, 0x60),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0, 0x200),
]

for name, rva, sz in targets:
    dump_annotated(name, rva, sz)
    dump_func_details(name, rva, sz)
