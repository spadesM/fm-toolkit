import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

dump_func_details("StreamedListView.set_Reorderable", 0x015ad4f0, 0x100)
dump_func_details("StreamedTable.get_IsDragCellActive", 0x015f2230, 0x100)
dump_func_details("StreamedTable.set_DragCellID", 0x015f2430, 0x100)
dump_func_details("StreamedTable.set_DragEvents", 0x015f2450, 0x100)
dump_func_details("StreamedTable.OnStartReorder", 0x015ee350, 0x200)
dump_func_details("StreamedTable.OnReorder", 0x015edbe0, 0x200)
dump_func_details("StreamedTable.OnEndReorder", 0x015ec410, 0x200)

for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if 'UxmlSerializedData' in name and ('StreamedTable' in name or 'StreamedListView' in name):
            print(f"0x{rva:08x}: {name}")
