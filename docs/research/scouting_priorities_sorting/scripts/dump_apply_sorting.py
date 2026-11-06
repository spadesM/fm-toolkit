from dump_headers_fast import dump_fast

targets = [
    ("StreamedListView.HasRowReceivedAllData (0x015a4040)", 0x015a4040, 0x015a4260),
    ("StreamedListView.ApplySorting (0x015a4260)", 0x015a4260, 0x015a4720),
    ("StreamedListView.BindSortPathNextDepth (0x015a4850)", 0x015a4850, 0x015a4b50),
]

for name, s, e in targets:
    dump_fast(name, s, e)
