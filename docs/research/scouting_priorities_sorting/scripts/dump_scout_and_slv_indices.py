import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf

# 1. SpecificallyScoutedPersonReference (0x00696ef0..0x00697800) and ScoutPlayerPrioritiesReference (0x0067d300..0x0067d700)
dhf.dump_fast("ScoutPlayerPrioritiesReference", 0x0067d300, 0x0067d700)
dhf.dump_fast("SpecificallyScoutedPersonReference", 0x00696ef0, 0x00697800)

# 2. StreamedListView methods using +0x568 (m_sortedIndices) and +0x604:
for label, s, e in [
    ("StreamedListView.GetItemFromView", 0x015a5a10, 0x015a5b90),
    ("StreamedListView.RefreshInternal", 0x015a9060, 0x015a9420),
    ("StreamedListView.ResetIndices", 0x015a9420, 0x015a9600),
    ("StreamedListView.Rebuild", 0x015a8eb0, 0x015a9060),
    ("StreamedListView.CanBuild", 0x015a50b0, 0x015a5180),
    ("StreamedListView.ShouldEnableContent", 0x015a9c20, 0x015a9c80),
    ("StreamedTable.OnBindItem", 0x015eb760, 0x015eba00),
    ("StreamedTable.OnRebindItem", 0x015ed7d0, 0x015edad0),
    ("StreamedTable.SetList", 0x015ef610, 0x015ef900),
]:
    dhf.dump_fast(label, s, e)
