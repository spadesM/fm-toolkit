import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

for name, rva in [
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.SetSorting(string, bool, ...)", 0x015efce0),
    ("StreamedListView.SetSortingBinding(2)", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
]:
    dump_func_details(name, rva)
