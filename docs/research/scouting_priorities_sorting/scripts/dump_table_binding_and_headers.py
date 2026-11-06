import sys
sys.stdout.reconfigure(encoding="utf-8")
from inspect_streamed_table_all import dump_with_strings

targets = [
    ("StreamedTable.BindToDataInternal", 0x015e6d70),
    ("StreamedTable.BindHeaders", 0x015e6ca0),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.CreateColumns", 0x015e83b0),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.InitialiseColumns", 0x015ea870),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.SetNoSorting", 0x015ef750),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.BindToData", 0x015a49b0),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
]

for name, rva in targets:
    dump_with_strings(name, rva)
