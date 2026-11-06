import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedTable_1501", 0x015ee900, 0x015ef1e0),
    ("StreamedListView_869", 0x015a5d00, 0x015a6200),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
