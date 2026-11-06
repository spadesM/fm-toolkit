import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

funcs = [
    ("StreamedListView.BindToData", 0x015a49b0, 0x700),
    ("StreamedListView.SetList", 0x015a9880, 0x350),
    ("StreamedListView.ResetIndices", 0x015a9420, 0x150),
    ("StreamedListView.GetItemFromView", 0x015a5a10, 0x120),
    ("StreamedListView.GetItemFromSource", 0x015a59e0, 0x50),
    ("SortComparer.Compare (int, int)", 0x015a3c60, 0xd0),
    ("SortComparer.Compare (ValueWrapper, ValueWrapper)", 0x015a3d30, 0x530),
    ("StreamedTable.UpdateSortColumn", 0x015f1380, 0x2d0),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)

print("\n=== All methods in range 0x015df000 .. 0x015f4000 ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015df000 <= rva <= 0x015f4000:
        print(f"  0x{rva:08x}: {rva_to_method_name[rva]}")
