import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va,
    dump_func_details, rva_to_end, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules
)

funcs = [
    ("SpecificallyScoutedPersonReference.get_Identifier", 0x00697370),
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("ScoutPlayerPrioritiesReference.get_Identifier", 0x0067d650),
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360),
    ("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.GetItemFromView", 0x015a5a10),
    ("StreamedListView.GetItemFromSource", 0x015a59e0),
    ("StreamedListView.OnBindItemInternal", 0x015a67d0),
    ("StreamedListView.OnRebindItemInternal", 0x015a7660),
    ("StreamedTable.CanBuild", 0x015e7580),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.SetSorting_1", 0x015efc40),
    ("StreamedTable.SetSorting_2", 0x015efce0),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
]

for name, rva in funcs:
    dump_func_details(name, rva)
