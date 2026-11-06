import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
from check_deep_sorting import rva_to_end, dump_func_details

targets = [
    ("SortComparer.Compare_2", 0x015a3d30),
    ("StreamedListView.BindToData", 0x015a49b0),
    ("StreamedListView.ClearSortingState", 0x015a5180),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.Rebuild", 0x015a8eb0),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.SetDirty", 0x015a9780),
    ("StreamedListView.SetList", 0x015a9880),
    ("StreamedListView.SetNoSorting", 0x015a99d0),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
]

for name, rva in targets:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dhf.dump_fast(name, rva, end_rva)
    dump_func_details(name, rva)
