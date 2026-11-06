from dump_headers_fast import dump_fast

targets = [
    ("StreamedListView.SetupRow", 0x015aa320, 0x015aa560),
    ("StreamedListView.RebindRow", 0x015a8f60, 0x015a9160),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x015a4af0),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a8eb0),
    ("Bindings.CreateScope_014bfa90", 0x014bfa90, 0x014bfb90),
    ("Bindings.CreateVariable_014bfb90", 0x014bfb90, 0x014bfd00),
    ("Bindings.SetAlias_014c6d50", 0x014c6d50, 0x014c6e50),
    ("StreamedTable.CreateHeaderCell_015dfab0", 0x015dfab0, 0x015dff00),
]

for name, s, e in targets:
    dump_fast(name, s, e)
