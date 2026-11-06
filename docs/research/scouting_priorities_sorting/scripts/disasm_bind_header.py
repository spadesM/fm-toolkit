import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import dump_func_details
from annotate_sorting_usym import dump_annotated

for name, rva in [
    ("Header.Bind", 0x015df4f0),
    ("Header.OnBindingChanged", 0x015df600),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.BindHeaders", 0x015e6ca0),
    ("StreamedTable.BindToDataInternal", 0x015e6d70),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.UpdateStreamedTableView", 0x015f1650),
    ("StreamedTable.CanBuild", 0x015e7580),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedListView.SetList", 0x015a9880),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
