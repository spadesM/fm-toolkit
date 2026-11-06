import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING ===")
for name, rva in [
    ("CreateColumnsFromTableViewCollection", 0x015e82c0),
    ("CreateColumnsFromTableView", 0x015e8350),
    ("CreateColumns", 0x015e83b0),
    ("CreateColumn", 0x015e7dc0),
    ("CreateHeader", 0x015e8f00),
    ("InitialiseColumns", 0x015ea870),
]:
    end = rva_to_end.get(rva, rva + 0x400)
    dump_func_details(name, rva, end - rva)
