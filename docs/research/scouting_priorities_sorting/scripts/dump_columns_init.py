from dump_streamed_table_sort import dump_fast

targets = [
    ("StreamedTable.UpdateStreamedTableView", 0x015f1650, 0x015f1760),
    ("StreamedTable.CreateColumn", 0x015e7dc0, 0x015e8170),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640, 0x015ec910),
    ("StreamedTable.OnViewSet", 0x015ee7a0, 0x015ee830),
    ("StreamedTable.CanPopulateTable", 0x015e7640, 0x015e7690),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0, 0x015e59b0),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70, 0x015f0040),
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80, 0x015a9ae0),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0, 0x015a9c20),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800, 0x015ab9b0),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0, 0x015a7ff0),
    ("StreamedListView..ctor", 0x015abdf0, 0x015ac200),
]

for name, start, end in targets:
    dump_fast(name, start, end)
