import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedListView_1420", 0x015a8ea0, 0x015a9200),
    ("StreamedListView_705_and_neighbors", 0x015aa650, 0x015ab000),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
