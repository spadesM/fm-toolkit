import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

for name, rva in [
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedTable.UpdateStreamedTableView", 0x015f1650),
]:
    dump_func_details(name, rva)
