import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from dump_headers_fast import dump_fast

dump_fast("StreamedListView_set_Reorderable", 0x015ad4d0, 0x015ad540)
dump_fast("StreamedListView_BindSortPathNextDepth", 0x015a4850, 0x015a49b0)
dump_fast("StreamedListView_OnSortingDataChanged", 0x015a7ff0, 0x015a8110)
dump_fast("StreamedListView_PostSortingDataChanged", 0x015a8610, 0x015a86c0)
dump_fast("StreamedListView_ProcessSortingDataChanged", 0x015a8cb0, 0x015a8eb0)
dump_fast("StreamedTable_OnStartReorder_OnReorder_OnEndReorder", 0x015ec410, 0x015ec640)
dump_fast("StreamedTable_OnReorder", 0x015edbe0, 0x015ee050)
dump_fast("StreamedTable_MakeColumnHeader_b_0", 0x015f0230, 0x015f0c00)
