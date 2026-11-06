import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast

ranges = [
    ("StreamedListView_857", 0x015a9b50, 0x015a9d00),
    ("StreamedListView_1549", 0x015ab580, 0x015ab700),
    ("StreamedListView_404", 0x015acdc0, 0x015ace50),
    ("StreamedTable_3393", 0x015e8380, 0x015e8480),
    ("StreamedTable_3114", 0x015e8b20, 0x015e8c20),
    ("StreamedTable_1415", 0x015eb880, 0x015eb980),
    ("StreamedTable_1321", 0x015ece50, 0x015ecf80),
    ("StreamedTable_3622", 0x015ee0d0, 0x015ee250),
    ("StreamedTable_2381", 0x015ef1e0, 0x015ef300),
    ("StreamedTable_3589", 0x015ef860, 0x015ef960),
    ("StreamedTable_603", 0x015f2200, 0x015f2350),
]
for name, s, e in ranges:
    dump_headers_fast.dump_fast(name, s, e)

