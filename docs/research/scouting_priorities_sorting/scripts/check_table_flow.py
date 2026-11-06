import check_deep_sorting as cds

targets = [
    ("StreamedTable.BindToDataInternal", 0x015e6d70, 1281),
    ("StreamedTable.SetList", 0x015ef610, 1029),
    ("StreamedTable.SetReorderable", 0x015efa20, 100),
    ("StreamedTable.OnMakeItem", 0x015ecc60, 742),
    ("StreamedTable.BindHeader", 0x015e6230, 800),
    ("StreamedListView.BindToDataInternal", 0x015a4c10, 700),
    ("StreamedListView.RefreshInternal", 0x015a9060, 800),
    ("StreamedListView.UpdateDisplay", 0x015a9be0, 400),
    ("StreamedListView.SetItemsSource", 0x015a96a0, 500),
    ("StreamedListView.OnBindItem", 0x015a6df0, 900),
]

for name, rva, sz in targets:
    cds.dump_func_details(name, rva, sz)
