import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("StreamedTable.CreateColumn", 0x015e7dc0, 0x3b0),
    ("StreamedTable.CreateHeader", 0x015e8f00, 0x1b0),
    ("StreamedTable.MakeColumnHeader", 0x015eac30, 0x3d0),
    ("StreamedTable.BindHeader", 0x015e6230, 0x350),
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 0x260),
    ("StreamedTable.EntryForColumn", 0x015e9450, 0x70),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
