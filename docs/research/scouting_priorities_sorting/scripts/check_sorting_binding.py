import check_deep_sorting as cds

targets = [
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.ClearSortingState", 0x015a5180),
    ("StreamedListView.BindToData", 0x015a49b0),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.CanBuild", 0x015e7580),
    ("StreamedTable.CanPopulateTable", 0x015e7640),
]

for name, rva in targets:
    cds.dump_func_details(name, rva)
