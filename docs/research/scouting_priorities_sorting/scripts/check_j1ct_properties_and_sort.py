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
    d.dump_fast(f"FourCC {name} registration at 0x{rva:08x}", rva, rva + 0x80)

# Also dump 0x00697200..0x00697800 to see ALL methods of SpecificallyScoutedPersonReference!
# Wait: earlier we saw 'cYEE' (0x63594545) at:
#   RVA=0x00696f28
#   RVA=0x0069706a
#   RVA=0x006972a6
#   RVA=0x0069738d
#   RVA=0x006974ba
#   RVA=0x006975fd
#   RVA=0x006976a1
# Let's dump 0x00697350..0x00697800!
d.dump_fast("0x00697350..0x00697800", 0x00697350, 0x00697800)
