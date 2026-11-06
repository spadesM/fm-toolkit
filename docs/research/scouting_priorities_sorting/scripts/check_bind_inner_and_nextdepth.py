import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x260),
    ("Bindings.GetProperties", 0x014c1a60, 0x200),
    ("Bindings.Bind_sub1 (0x014beef0)", 0x014beef0, 0x360),
    ("Bindings.Bind_sub2 (0x014bf250)", 0x014bf250, 0x360),
    ("Bindings.MarkNodeDirty (0x014c2350)", 0x014c2350, 0x150),
    ("Bindings.Update (+0xbe0)", 0x014c7650, 0x500),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
