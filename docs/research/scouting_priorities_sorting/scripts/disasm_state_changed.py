import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import dump_headers_fast as dhf

dhf.dump_fast("StreamedListView.StateChanged", 0x015a9c80, 0x015a9ed7)
dhf.dump_fast("StreamedListView.ResolveStateChanges", 0x015a9620, 0x015a9667)
dhf.dump_fast("StreamedListView.RefreshInternal", 0x015a9060, 0x015a9387)
dhf.dump_fast("StreamedTable.RefreshInternal", 0x015eed80, 0x015eef42)
dhf.dump_fast("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x015a86bf)
dhf.dump_fast("StreamedListView.HasSorting", 0x015a5f20, 0x015a5ffa)
