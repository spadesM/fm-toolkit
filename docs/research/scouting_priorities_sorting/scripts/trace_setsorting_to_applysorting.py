import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

for label, rva in [
    ("StreamedTable.SetSorting(1)", 0x015efc40),
    ("StreamedTable.SetSorting(2)", 0x015efce0),
    ("StreamedListView.SetSortingBinding(2)", 0x015a9ae0),
    ("StreamedListView.ApplySorting", 0x015a4260),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedTable.RefreshInternal", 0x015eed80),
]:
    dump_func_details(label, rva)
