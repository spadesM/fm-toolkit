import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

ranges = [
    ("StreamedListView_880_930", 0x015a4200, 0x015a4850),
    ("StreamedListView_990", 0x015a5100, 0x015a5350),
    ("StreamedListView_735_775", 0x015a8c80, 0x015a9000),
    ("StreamedListView_570", 0x015ac9e0, 0x015acb50),
]
for name, s, e in ranges:
    dhf.dump_fast(name, s, e)
