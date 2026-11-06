import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

funcs = [
    ("StreamedTable.CanBuild", 0x015e7580),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.CreateColumns", 0x015e83b0),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.SetSortingBinding(1)", 0x015a9a80),
    ("StreamedListView.SetSortingBinding(2)", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
]

for label, rva in funcs:
    dump_func_details(label, rva)
