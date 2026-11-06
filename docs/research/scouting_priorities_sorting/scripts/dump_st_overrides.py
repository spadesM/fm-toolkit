import struct
from dump_sorting_core import dump_clean

dump_clean("StreamedTable.RefreshInternal", 0x015eed80, 450)
dump_clean("StreamedTable.OnRebindItem", 0x015ed7d0, 400)
dump_clean("StreamedTable.BindToDataInternal", 0x015e6d70, 600)
dump_clean("StreamedTable.RebuildInternal", 0x015ee9c0, 270)
dump_clean("StreamedTable.CreateHeader", 0x015e8f00, 300)
dump_clean("StreamedTable.UpdateSortColum", 0x015f1380, 330)
dump_clean("StreamedTable.EntryForColumn", 0x015e9450, 110)
dump_clean("StreamedTable.TryFindSortedColumn", 0x015eff70, 200)
