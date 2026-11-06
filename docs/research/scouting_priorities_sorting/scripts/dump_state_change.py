from dump_headers_fast import dump_fast

targets = [
    ("StreamedListView.BeginStateChange (0x015a47a0)", 0x015a47a0, 0x015a4850),
    ("StreamedListView.EndStateChange (0x015a5350)", 0x015a5350, 0x015a53a0),
    ("StreamedListView.StateChanged (0x015a9c80)", 0x015a9c80, 0x015a9ee0),
    ("StreamedListView.SetList (0x015a9880)", 0x015a9880, 0x015a9a80),
    ("StreamedTable.SetList (0x015ef610)", 0x015ef610, 0x015ef750),
    ("StreamedTable.SetNoSorting (0x015ef750)", 0x015ef750, 0x015ef890),
]

for name, s, e in targets:
    dump_fast(name, s, e)
