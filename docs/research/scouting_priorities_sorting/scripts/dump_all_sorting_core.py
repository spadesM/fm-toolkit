import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

from check_sorting_details import dump_fast

targets = [
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0, 0x00696f70),
    ("SpecificallyScoutedPersonReference.GetPropertyInternal", 0x00696f70, 0x006971c0),
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 0x015ecce0),
    ("StreamedTable.SetSorting(1)", 0x015efc40, 0x015efce0),
    ("StreamedTable.SetSorting(2)", 0x015efce0, 0x015f0040),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x015f0230),
    ("StreamedListView.SetSortingBinding", 0x015a9ae0, 0x015a9df0),
    ("StreamedListView.ApplySorting", 0x015a4260, 0x015a4850),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x015a4a30),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a9600),
    ("StreamedListView.SetupRow", 0x015aa320, 0x015aa630),
]

for name, start, end in targets:
    dump_fast(name, start, end)
