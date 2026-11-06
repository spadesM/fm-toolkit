import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedTable_1740_and_1538", 0x015e6200, 0x015e7200),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
