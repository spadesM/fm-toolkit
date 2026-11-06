from dump_streamed_table_sort import dump_fast

targets = [
    ("StreamedListView.SetSorting<T> (0x00abdcc0)", 0x00abdcc0, 0x00abe050),
    ("StreamedTable.SetSorting_1 (0x015efc40)", 0x015efc40, 0x015efce0),
    ("StreamedTable.SetSorting_2 (0x015efce0)", 0x015efce0, 0x015eff70),
    ("StreamedTable.TrySetColumnsAndSort (0x015f0040)", 0x015f0040, 0x015f0230),
]

for name, start, end in targets:
    dump_fast(name, start, end)
