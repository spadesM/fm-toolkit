import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

funcs = [
    ("StreamedTable.CreateColumns", 0x015e83b0, 0x220),
    ("StreamedTable.CreateColumnsFromTableView", 0x015e8350, 0x60),
    ("StreamedTable.CreateColumnsFromTableViewCollection", 0x015e82c0, 0x90),
    ("StreamedTable.InitialiseColumns", 0x015ea870, 0x190),
    ("StreamedTable.OnViewSet", 0x015ee7a0, 0x90),
    ("StreamedTable.<OnViewSet>b__297_0", 0x015f0800, 0x30),
    ("StreamedTable.CanBuild", 0x015e7580, 0xc0),
    ("StreamedTable.CanPopulateTable", 0x015e7640, 0x50),
    ("StreamedTable.RebuildInternal", 0x015ee9c0, 0x110),
    ("StreamedTable.RefreshInternal", 0x015eed80, 0x1d0),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640, 0x2d0),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)

print("\n=== All StreamedListView methods ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015a3000 <= rva <= 0x015b2000:
        print(f"  0x{rva:08x}: {rva_to_method_name[rva]}")
