import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import rva_to_method_name, dump_func_details

funcs = [
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 0x350),
    ("Bindings.Bind", 0x014bee30, 0x200),
    ("Bindings.Bind_inner (0x014be6c0)", 0x014be6c0, 0x310),
    ("MarkChildrenDirtyRecursive? (0x014c22e0)", 0x014c22e0, 0x200),
    ("MarkNodeDirty? (0x014c2450)", 0x014c2450, 0x200),
    ("Bindings.Update (+0x550)", 0x014c6fc0, 0x700),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x400),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
