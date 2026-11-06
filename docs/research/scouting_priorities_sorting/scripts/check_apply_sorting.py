import check_deep_sorting as cds

targets = [
    ("Func_0x00abdcc0", 0x00abdcc0, 800),
    ("StreamedListView.ApplySorting", 0x015a4260, None),
    ("StreamedListView.SetupRow", 0x015aa320, None),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, None),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0, None),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, None),
    ("SortData.HasReceived", 0x015a4040, None),
]

for name, rva, sz in targets:
    cds.dump_func_details(name, rva, sz)
