import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

# 1. Dump USYM files around RVA 0x00696000..0x00698000
print("=== 1. USYM in 0x00696000..0x00698500 ===")
lo, hi = 0, d.sym_count - 1
while lo < hi:
    mid = (lo + hi) // 2
    rva = struct.unpack_from("<I", d.udata, d.records_off + mid * 24)[0]
    if rva < 0x00696000: lo = mid + 1
    else: hi = mid
for idx in range(max(0, lo - 5), min(d.sym_count, lo + 400)):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", d.udata, d.records_off + idx * 24)
    if rva > 0x00698500: break
    fn = d.get_ustr(file_off).split("/")[-1].split("\\")[-1]
    sym = d.get_ustr(sym_off)
    print(f"  0x{rva:08x} {fn}:{line} {sym}")

# 2. Dump 0x00696f00..0x00697600
d.dump_fast("SpecificallyScoutedPersonReference area", 0x00696f00, 0x00697600)

# 3. Check what [0x02e06ea8] and [0x02dcbd30] and [0x0303b8c0] are in ProcessSortValue (StreamedListView.cs:756) and StreamedListView.cs:1969
for va_rva in [0x02e06ea8, 0x02dcbd30, 0x0303b8c0, 0x02e1c298]:
    foff = d.va_to_off(d.image_base + va_rva)
    val = struct.unpack_from("<Q", d.pe, foff)[0]
    tag = (val & 0xFFFFFFFF) >> 29
    idx = ((val & 0xFFFFFFFF) & 0x1FFFFFFF) >> 1
    print(f"RVA 0x{va_rva:08x}: raw=0x{val:016x} tag={tag} idx={idx} lit={d.get_lit(idx)!r}")
    if 0 <= idx * 88 < d.types_sz:
        tu = struct.unpack_from("<22i", d.meta, d.types_off + idx * 88)
        print(f"   if TypeDef[{idx}]: {d.get_mstr(tu[1])}.{d.get_mstr(tu[0])}")
