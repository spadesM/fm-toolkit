import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details
from annotate_sorting_usym import dump_annotated

targets = [
    ("StreamedListView.SetSortingBinding(1)", 0x015a9a80),
    ("StreamedListView.SetSortingBinding(2)", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.GetItemFromView", 0x015a5a10),
    ("StreamedListView.GetItemFromSource", 0x015a59e0),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.BindToDataInternal", 0x015a4a20),
    ("StreamedListView.RebuildInternal", 0x015a8f60),
    ("StreamedListView.RefreshView", 0x015a92a0),
]

for name, rva in targets:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
