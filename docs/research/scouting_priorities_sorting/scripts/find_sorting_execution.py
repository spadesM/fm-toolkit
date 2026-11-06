import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

udata = dhf.udata
sym_count = dhf.sym_count
records_off = dhf.records_off

lo, hi = 0, sym_count - 1
target = 0x015a3000
while lo < hi:
    mid = (lo + hi) // 2
    rva = struct.unpack_from("<I", udata, records_off + mid * 24)[0]
    if rva < target:
        lo = mid + 1
    else:
        hi = mid

print("=== Functions in 0x015a3000..0x015f3000 ===")
last_line_group = None
for idx in range(lo, sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    if rva > 0x015f3000:
        break
    if file_off == 0:
        continue
    fn = dhf.get_ustr(file_off).split("/")[-1].split("\\")[-1]
    if fn in ("StreamedListView.cs", "StreamedTable.cs"):
        if last_line_group is None or rva - last_line_group[1] > 0x30 or abs(line - last_line_group[4]) > 40 or fn != last_line_group[2]:
            if last_line_group:
                print(f"  0x{last_line_group[0]:08x}..0x{last_line_group[1]:08x}: {last_line_group[2]:20s} lines {last_line_group[3]:4d}..{last_line_group[4]:4d}")
            last_line_group = [rva, rva, fn, line, line]
        else:
            last_line_group[1] = rva
            last_line_group[3] = min(last_line_group[3], line)
            last_line_group[4] = max(last_line_group[4], line)
if last_line_group:
    print(f"  0x{last_line_group[0]:08x}..0x{last_line_group[1]:08x}: {last_line_group[2]:20s} lines {last_line_group[3]:4d}..{last_line_group[4]:4d}")
