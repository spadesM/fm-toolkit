import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("StreamedListView.SetSortingBinding (1)", 0x015a9a80, 0x60),
    ("StreamedListView.SetSortingBinding (2)", 0x015a9ae0, 0x140),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800, 0x1b0),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0, 0x350),
    ("StreamedListView.RefreshInternal", 0x015a9060, 0x330),
    ("StreamedListView.ResolveStateChanges", 0x015a9620, 0x50),
    ("StreamedListView.EndStateChange", 0x015a5350, 0x50),
    ("StreamedTable.<.ctor>b__206_0", 0x015f0a70, 0xc0),
    ("StreamedTable.<.ctor>b__206_1", 0x015f0b30, 0xc0),
    ("StreamedTable.<.ctor>b__206_2", 0x015f0bf0, 0x10),
    ("StreamedListView.<BindToData>b__232_0", 0x015af210, 0xa0),
    ("StreamedListView.<BindToData>b__232_1", 0x015af2b0, 0xa0),
    ("StreamedListView.<.ctor>b__231_0", 0x015af430, 0x310),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
