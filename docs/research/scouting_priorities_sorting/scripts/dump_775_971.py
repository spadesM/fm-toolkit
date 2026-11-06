import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedListView_770_800", 0x015a7fd0, 0x015a8900),
    ("StreamedListView_971_985", 0x015a99c0, 0x015a9c50),
    ("StreamedListView_293", 0x015acd30, 0x015acdc0),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
