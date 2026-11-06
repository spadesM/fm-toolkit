import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x350),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x450),
    ("Bindings.GetNthProperty", 0x014c1450, 0x200),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
