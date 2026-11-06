import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

for name, rva in [
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedTable.GeneratePersistenceKeys", 0x015e9600),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.SetNoSorting", 0x015ef750),
]:
    dump_func_details(name, rva)
