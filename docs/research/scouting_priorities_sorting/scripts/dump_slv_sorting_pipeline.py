import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

funcs = [
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.SetNoSorting", 0x015a99d0),
    ("StreamedListView.ClearSortingState", 0x015a5180),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
]

for name, rva in funcs:
    dump_func_details(name, rva)
