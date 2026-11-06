import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

# 1. Search for fourcc 'cYEE' (0x63594545) and 'uDc3' (0x75446333) in GameAssembly.dll
for label, val in [("cYEE", 0x63594545), ("uDc3", 0x75446333), ("dMxa", 0x644d7861)]:
    pat = struct.pack("<I", val)
    pos = 0
    print(f"=== Search {label} (0x{val:08x}) ===")
    while True:
        idx = d.pe.find(pat, pos)
        if idx < 0: break
        for name, vaddr, vsize, raddr, rsize in d.sections:
            if raddr <= idx < raddr + rsize:
                rva = vaddr + (idx - raddr)
                print(f"  RVA=0x{rva:08x} sec={name}")
        pos = idx + 1

# 2. Dump StreamedTable.cs ranges in chunks of <= 1800 bytes so get_usym_dict doesn't truncate
ranges = [
    ("StreamedTable ctor & props 1", 0x015f1930, 0x015f2100),
    ("StreamedTable props 2", 0x015f2100, 0x015f2960),
    ("StreamedTable headers 1 (1740..1887)", 0x015e6230, 0x015e6900),
    ("StreamedTable headers 2 (1740..1887)", 0x015e6900, 0x015e6d70),
    ("StreamedTable cols (1518..1626)", 0x015e6d70, 0x015e7580),
    ("StreamedTable sorting helpers (1725..2266)", 0x015e8e40, 0x015e94c0),
]
for name, s, e in ranges:
    d.dump_fast(name, s, e)
