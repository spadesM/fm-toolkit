import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import dump_with_strings
from check_deep_sorting import rva_to_method_name

# List all methods of Header
for rva in sorted(rva_to_method_name):
    for name in rva_to_method_name[rva]:
        if "Header." in name or "StreamedTable." in name:
            print(f"0x{rva:08x}: {name}")

dump_with_strings("Header..ctor (0x015dfab0)", 0x015dfab0, 0x350)
dump_with_strings("StreamedTable.UpdatePersistedColumnSortingData (0x015f1290)", 0x015f1290, 0x150)
dump_with_strings("StreamedTable.SetSorting_1 (0x015efc40)", 0x015efc40, 0x100)
dump_with_strings("StreamedListView.EndStateChange (0x015a5350)", 0x015a5350, 0x100)
dump_with_strings("StreamedListView.AsStreamedObjectList (0x015a4720)", 0x015a4720, 0x100)
