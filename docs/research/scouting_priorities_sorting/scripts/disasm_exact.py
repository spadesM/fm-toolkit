from dump_headers_fast import dump_fast

targets = [
    ("0x00292620", 0x00292620, 0x00292670),
    ("StreamedTable.CanBuild", 0x015e7580, 0x015e7640),
    ("StreamedTable.RebuildInternal", 0x015ee9c0, 0x015eead0),
    ("StreamedTable.CreateColumns", 0x015e83b0, 0x015e85d0),
    ("StreamedTable.OnSortColumn", 0x015ee250, 0x015ee290),
    ("StreamedTable.UpdateSortColum", 0x015f1380, 0x015f14d0),
    ("StreamedTable.SetNoSorting", 0x015ef750, 0x015ef890),
    ("StreamedListView.SetNoSorting", 0x015a99d0, 0x015a9a80),
]

for name, start, end in targets:
    dump_fast(name, start, end)
