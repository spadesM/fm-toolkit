import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

dump_func_details("StreamedTable.get_DisableSorting", 0x015f2190, 0x40)
dump_func_details("StreamedTable.set_DisableSorting", 0x015f2420, 0x40)
dump_func_details("StreamedTable.get_SortedColumn", 0x015f2360, 0x40)
dump_func_details("StreamedTable.set_SortedColumn", 0x015f2930, 0x40)

# Find StreamedTable.UxmlSerializedData.Deserialize
for rva, names in sorted(rva_to_method_name.items()):
    if 0x015a0000 <= rva <= 0x015fffff:
        for name in names:
            if 'Deserialize' in name:
                print(f"0x{rva:08x}: {name}")
                dump_func_details(name, rva, 0xa00)
