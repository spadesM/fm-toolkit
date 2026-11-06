import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

targets = [
    ("StreamedListView.get_ReceivedAllSortingData", 0x015acd40),
    ("StreamedListView.BeginStateChange(0)", 0x015a47a0),
    ("StreamedListView.BeginStateChange(1)", 0x015a47f0),
    ("StreamedListView.SetDirty", 0x015a9780),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
]

for name, rva in targets:
    dump_func_details(name, rva)
