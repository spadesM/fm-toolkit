import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, pe, rva_to_method_name

funcs = [
    ("SetSortingBinding<T> (0x00abdcc0)", 0x00abdcc0, 0x200),
    ("StreamedTable.UpdatePersistedColumnSortingData", 0x015f1290, 0xf0),
    ("StreamedTable.GeneratePersistenceKeys", 0x015e9600, 0x310),
    ("StreamedTable.MakeDefaultSelectedColumnHeader", 0x015eb000, 0xe0),
    ("StreamedTable.EntryForColumn", 0x015e9450, 0x70),
    ("StreamedTable.UpdateCustomViewDropdown", 0x015f10f0, 0x1a0),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
