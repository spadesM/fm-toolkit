import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')

import check_900_dict
print("\n" + "="*80 + "\n")
import find_7_props_and_trace
print("\n" + "="*80 + "\n")
from annotate_sorting_usym import dump_annotated

targets = [
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.SetSorting(string, bool, ...)", 0x015efce0),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
    ("StreamedListView.SetSortingBinding(1)", 0x015a9a80),
    ("StreamedListView.SetSortingBinding(2)", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
]

for name, rva in targets:
    dump_annotated(name, rva)
