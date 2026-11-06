import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedTable_2100", 0x015ef500, 0x015ef890),
    ("StreamedListView_1232", 0x015a9c50, 0x015a9f50),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
