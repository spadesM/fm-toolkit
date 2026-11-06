import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

funcs = [
    ("StreamedListView.set_Reorderable", 0x015ad4f0, 0x40),
    ("StreamedTable.get_IsDragCellActive", 0x015f2230, 0x30),
    ("StreamedTable.set_DragCellID", 0x015f2430, 0x30),
    ("StreamedTable.OnStartReorder", 0x015ee350, 0x310),
    ("StreamedTable.OnReorder", 0x015edbe0, 0x470),
    ("StreamedTable.OnEndReorder", 0x015ec410, 0x230),
    ("StreamedListView.UxmlSerializedData.Deserialize", 0x015b0b50, 0x500),
]

for name, rva, sz in funcs:
    dump_func_details(name, rva, sz)
