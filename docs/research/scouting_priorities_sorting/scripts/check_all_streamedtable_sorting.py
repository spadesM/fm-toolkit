import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import rva_to_method_name, dump_func_details

for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if "StreamedTable" in name or "StreamedListView" in name:
            print(f"0x{rva:08x}: {name}")
