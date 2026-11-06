import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

fourccs = [
    ("plyr", 0x0046ede5),
    ("dMxa", 0x0046b097),
    ("cYEE", 0x0046cb53),
    ("uDc3", 0x00468d8f),
    ("quLv", 0x00468ca3),
    ("sqN ", 0x00468c2d),
    ("nGWs", 0x00468bb7),
]
for name, rva in fourccs:
    d.dump_fast(f"FourCC {name} at 0x{rva:08x}", rva - 0x08, rva + 0x48)

ranges = [
    ("StreamedTable.cs:1188..1230 (0x015f0040..0x015f0230)", 0x015f0040, 0x015f0230),
    ("StreamedTable.cs:1725..1738 & 2106..2114 (0x015e8f00..0x015e90b0 & 0x015eb000..0x015eb0e0)", 0x015e8f00, 0x015e90b0),
    ("StreamedTable.cs:2106..2114 (0x015eb000..0x015eb0e0)", 0x015eb000, 0x015eb0e0),
    ("StreamedTable.cs:2159..2178 (0x015ec2d0..0x015ec390)", 0x015ec2d0, 0x015ec390),
    ("StreamedTable.cs:2269..2330 (0x015eac30..0x015eb000)", 0x015eac30, 0x015eb000),
    ("StreamedTable.cs:2424..2650 (0x015e57e0..0x015e58c0)", 0x015e57e0, 0x015e58c0),
]
for name, s, e in ranges:
    d.dump_fast(name, s, e)
