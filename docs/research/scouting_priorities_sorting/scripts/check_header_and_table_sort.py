import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("Header.Bind", 0x015df4f0, 0x110),
    ("Header.OnBindingChanged", 0x015df600, 0x120),
    ("Header.ResetSortingIcons", 0x015df720, 0x70),
    ("Header.SetupClickHandler", 0x015df7e0, 0xa0),
    ("Header.Unbind", 0x015df880, 0xf0),
    ("Header.UpdateSortingIcons", 0x015df970, 0xb0),
    ("Header..ctor", 0x015dfab0, 0x2b0),
    ("StreamedTable.SetSorting (1)", 0x015efc40, 0xa0),
    ("StreamedTable.SetSorting (2)", 0x015efce0, 0x290),
    ("StreamedTable.SetNoSorting", 0x015ef750, 0x140),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70, 0xd0),
    ("StreamedTable.OnSortColumn", 0x015ee250, 0x40),
    ("StreamedTable.SetList", 0x015ef610, 0x140),
    ("StreamedTable.OnBindItem", 0x015eb760, 0x3a0),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580, 0x280),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
