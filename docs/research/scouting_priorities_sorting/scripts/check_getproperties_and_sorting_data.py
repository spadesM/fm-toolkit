import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("Bindings.GetProperties", 0x014c1a60, 0x200),
    ("sub_00e030e0", 0x00e030e0, 0x150),
    ("StreamedTable.UpdatePersistedColumnSortingData", 0x015f1290, 0xf0),
    ("StreamedListView.UpdateEnabledState", 0x015aab80, 0x200),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x200),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 0x120),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610, 0xb0),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
