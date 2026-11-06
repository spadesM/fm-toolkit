import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

# 1. Check fourcc registrations in 0x00460000..0x00475000 for SpecificallyScoutedPersonReference's 7 properties:
# 'plyr' (0x706c7972), 'dMxa' (0x644d7861), 'cYEE' (0x63594545), 'uDc3' (0x75446333),
# 'quLv' (0x71754c76), 'sqN ' (0x73714e20), 'nGWs' (0x6e475773), and 'J1Ct' (0x7443314A)
print("=== 1. FourCC registrations in AutogenBindings ===")
fourccs = [
    ("J1Ct", 0x7443314A),
    ("plyr", 0x706c7972),
    ("dMxa", 0x644d7861),
    ("cYEE", 0x63594545),
    ("uDc3", 0x75446333),
    ("quLv", 0x71754c76),
    ("sqN ", 0x73714e20),
    ("nGWs", 0x6e475773),
]
for name, val in fourccs:
    pat = struct.pack("<I", val)
    pos = 0
    while True:
        idx = d.pe.find(pat, pos)
        if idx < 0: break
        for sname, vaddr, vsize, raddr, rsize in d.sections:
            if raddr <= idx < raddr + rsize:
                rva = vaddr + (idx - raddr)
                if 0x00450000 <= rva <= 0x00480000:
                    # dump 32 bytes before and after to see the string literal!
                    d.dump_fast(f"FourCC {name} at 0x{rva:08x}", rva - 0x20, rva + 0x20)
        pos = idx + 1

# 2. Search StreamedTable (0x015de910..0x015f3000) for offset 0x9b8 (b8 09 00 00) and 0x648 (48 06 00 00)
print("\n=== 2. Offsets 0x9b8 (m_disableSorting) and 0x648 (m_reorderable) in StreamedListView & StreamedTable ===")
off_start = d.va_to_off(d.image_base + 0x015a3ea0)
off_end = d.va_to_off(d.image_base + 0x015f3000)
chunk = d.pe[off_start:off_end]
for label, pat in [("0x9b8 (m_disableSorting)", b"\xb8\x09\x00\x00"), ("0x648 (m_reorderable)", b"\x48\x06\x00\x00"), ("0x604 (m_isSorted)", b"\x04\x06\x00\x00")]:
    print(f"--- {label} ---")
    p = 0
    while True:
        idx = chunk.find(pat, p)
        if idx < 0: break
        rva = 0x015a3ea0 + idx
        umap = d.get_usym_dict(rva - 0x20, 0x40)
        lines = [v for k, v in sorted(umap.items())]
        print(f"  0x{rva:08x}: {lines[-1] if lines else []}")
        p = idx + 1
