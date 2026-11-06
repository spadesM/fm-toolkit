import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

targets = [
    ("StreamedTable.get_IsDragCellActive", 0x015f2230, 0x015f2290),
    ("StreamedTable.set_DragCellID", 0x015f2430, 0x015f2490),
    ("StreamedTable.BindToDataInternal", 0x015e6d70, 0x015e7690),
    ("StreamedTable.CreateColumnsFromTableViewCollection", 0x015e82c0, 0x015e83b0),
    ("StreamedTable.OnMakeItem", 0x015ecc60, 0x015ed340),
    ("StreamedTable.OnBindItem", 0x015eb760, 0x015ebb00),
    ("StreamedListView.set_SourceData", 0x015ad680, 0x015ad950),
    ("StreamedListView.BindToData", 0x015a49b0, 0x015a5180),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x015a8cb0),
    ("StreamedListView.HasSorting", 0x015a5f20, 0x015a6080),
    ("StreamedListView.GetItemFromView_Source", 0x015a59e0, 0x015a5b90),
    ("StreamedListView.OnBindItemInternal", 0x015a67d0, 0x015a6870),
]

for name, s, e in targets:
    dhf.dump_fast(name, s, e)
