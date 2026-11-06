import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("0x010e4ed0 (Dict method in MakeColumnHeader)", 0x010e4ed0, 0x100),
    ("Header..ctor (0x015dfab0)", 0x015dfab0, 0x350),
    ("StreamedTable.CreateHeader (0x015e8f00)", 0x015e8f00, 0x200),
    ("StreamedTable.RecreateHeaders (0x015eecb0)", 0x015eecb0, 0x150),
    ("StreamedTable.CreateColumns (0x015e83b0)", 0x015e83b0, 0x250),
    ("StreamedTable.InitialiseColumns (0x015ea870)", 0x015ea870, 0x200),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
