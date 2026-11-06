import sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

targets = [
    ("StreamedTable.CreateHeader", 0x015e8f00, 0x015e90b0),
    ("StreamedTable.MakeColumnHeader", 0x015eac30, 0x015eb050),
    ("StreamedTable_0x015ec280_to_0x015ed400", 0x015ec280, 0x015ed400),
    ("StreamedTable.SetSorting_1_and_2", 0x015efc40, 0x015eff70),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0, 0x015a9c20),
    ("StreamedListView.ApplySorting_and_BindSortPathNextDepth", 0x015a4260, 0x015a4a50),
    ("StreamedListView.SetupRow", 0x015aa320, 0x015aa600),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a9060),
]

for name, s, e in targets:
    dump_fast(name, s, e)
