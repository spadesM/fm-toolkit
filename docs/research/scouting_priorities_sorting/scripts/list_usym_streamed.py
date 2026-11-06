import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from dump_headers_fast import udata, sym_count, records_off, get_ustr

lo, hi = 0, sym_count - 1
while lo < hi:
    mid = (lo + hi) // 2
    rva = struct.unpack_from("<I", udata, records_off + mid * 24)[0]
    if rva < 0x01590000: lo = mid + 1
    else: hi = mid

by_file = {}
for idx in range(lo, sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    if rva > 0x01610000: break
    fn = get_ustr(file_off).split("/")[-1].split("\\")[-1]
    if fn in ("StreamedListView.cs", "StreamedTable.cs"):
        sname = get_ustr(sym_off)
        by_file.setdefault(fn, []).append((rva, line, sname))

for fn, items in sorted(by_file.items()):
    print(f"\n=== {fn} ({len(items)} records) ===")
    last_rva = -1000
    last_line = -1000
    for rva, line, sname in items:
        if rva - last_rva > 0x20 or abs(line - last_line) > 5:
            print(f"  RVA 0x{rva:08x} : line {line:4d} {sname}")
            last_rva = rva
            last_line = line
