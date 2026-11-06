import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

ranges = [
    ("StreamedListView.cs:404 (0x015acdf0)", 0x015acd80, 0x015acf00),
    ("StreamedTable.cs:797..816 (0x015f14d0)", 0x015f14d0, 0x015f1650),
    ("StreamedTable.cs:1272..1435 (0x015ecc60..0x015ebaf4)", 0x015eb750, 0x015ebaf8),
    ("StreamedTable.cs:1272..1388 (0x015ecc60..0x015ed340)", 0x015ecc60, 0x015ed340),
    ("StreamedTable.cs:2377..2424 (0x015ef1e0..0x015ef450)", 0x015ef1e0, 0x015ef450),
    ("StreamedTable.cs:3389..3427 (0x015e83b0..0x015e85d0)", 0x015e83b0, 0x015e85d0),
    ("StreamedTable.cs:3567..3606 (0x015ee6e0..0x015ee830 & 0x015ef890..0x015efc40)", 0x015ee6e0, 0x015ee830),
    ("StreamedTable.cs:3586..3606 (0x015ef890..0x015efc40)", 0x015ef890, 0x015efc40),
    ("StreamedTable.cs:3692..3714 (0x015ed4c0..0x015ed5d0)", 0x015ed4c0, 0x015ed5d0),
]
for name, s, e in ranges:
    d.dump_fast(name, s, e)
