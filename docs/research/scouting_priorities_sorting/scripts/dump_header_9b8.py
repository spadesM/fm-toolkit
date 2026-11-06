import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

print("0x00292620 names:", rva_to_method_name.get(0x00292620))
dump_func_details("0x00292620", 0x00292620, 0x30)
dump_func_details("StreamedTable.CreateHeader", 0x015e8f00, 0x200)
dump_func_details("StreamedTable.MakeColumnHeader", 0x015eac30, 0x3d0)
dump_func_details("StreamedTable.MakeDefaultSelectedColumnHeader", 0x015eb000, 0x100)
dump_func_details("StreamedTable.OnMakeItem (+0x500..+0x750)", 0x015ecc60 + 0x500, 0x250)
