import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

targets = [
    ("Dict_Method_0x010e4ed0", 0x010e4ed0, 0x010e4f50),
    ("StreamedTable_0x015ef900_to_0x015efc40", 0x015ef900, 0x015efc40),
    ("StreamedTable_0x015f0040_to_0x015f0d10", 0x015f0040, 0x015f0d10),
    ("StreamedListView_0x015aa600_to_0x015ab800", 0x015aa600, 0x015ab800),
]

for name, s, e in targets:
    dhf.dump_fast(name, s, e)
