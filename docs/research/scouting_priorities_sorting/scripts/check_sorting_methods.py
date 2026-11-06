import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
from check_deep_sorting import dump_func_details

for name, rva in [
    ("StreamedTable.get_IsDragCellActive", 0x015f2230),
    ("StreamedTable.SetSorting_1", 0x015efc40),
    ("StreamedTable.SetSorting_2", 0x015efce0),
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.UpdateEnabledState", 0x015aab80),
]:
    dump_func_details(name, rva)
