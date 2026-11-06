import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import pe, meta, methods_off, types_off, get_mstr, image_base, va_to_off, get_usym_dict, sections

# Find all occurrences of specific struct offsets in StreamedListView (0x015a0000..0x015b5000) and StreamedTable (0x015e5000..0x015f5000) and VirtualisedList (0x016a5000..0x016b0000)
ranges = [
    ("StreamedListView", 0x015a3000, 0x015b0000),
    ("StreamedTable", 0x015e5000, 0x015f3000),
    ("VirtualisedList", 0x016a5000, 0x016ad000),
]

patterns = {
    "0x93d (DisableSorting)": b"\x3d\x09\x00\x00",
    "0x93c (UseRadioButtons)": b"\x3c\x09\x00\x00",
    "0x8e0 (m_sortedColumns)": b"\xe0\x08\x00\x00",
    "0x568 (m_itemView)": b"\x68\x05\x00\x00",
    "0x5c1 (list+0x5c1 reorderable?)": b"\xc1\x05\x00\x00",
    "0x4c1 (list+0x4c1)": b"\xc1\x04\x00\x00",
    "0x5c0 (list+0x5c0)": b"\xc0\x05\x00\x00",
}

for rname, s_rva, e_rva in ranges:
    off = va_to_off(image_base + s_rva)
    chunk = pe[off : off + (e_rva - s_rva)]
    print(f"=== {rname} (0x{s_rva:08x}..0x{e_rva:08x}) ===")
    for pname, pat in patterns.items():
        pos = 0
        hits = []
        while True:
            idx = chunk.find(pat, pos)
            if idx < 0: break
            rva = s_rva + idx
            umap = get_usym_dict(rva - 6, 16)
            uinfo = ""
            for k in sorted(umap.keys()):
                uinfo = ", ".join(umap[k])
                if uinfo: break
            hits.append(f"0x{rva:08x} ({uinfo})")
            pos = idx + 1
        if hits:
            print(f"  {pname}:")
            for h in hits:
                print(f"    {h}")
