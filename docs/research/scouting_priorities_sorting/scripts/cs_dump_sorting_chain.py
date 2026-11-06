import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from cs_disasm import disasm, find_rva
out = open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\cs_sorting_chain.txt", "w", encoding="utf-8")
names = [
    "StreamedTable.OnHeaderClicked",
    "StreamedTable.SetSorting",
    "StreamedListView.SetSortingBinding",
    "StreamedListView.ApplySorting",
    "StreamedListView.OnSortingDataChanged",
    "StreamedListView.ProcessSortingDataChanged",
    "StreamedListView.PostSortingDataChanged",
    "StreamedListView.get_ReceivedAllSortingData",
    "StreamedListView.BindSortPathNextDepth",
    "StreamedListView.RefreshInternal",
    "StreamedTable.SetList",
    "StreamedListView.SetList",
    "StreamedListView.BindToData",
]
for n in names:
    for r, full in find_rva(n):
        if full.startswith(n.split(".")[0] + "."):
            disasm(r, label=full, out=out)
out.close()
