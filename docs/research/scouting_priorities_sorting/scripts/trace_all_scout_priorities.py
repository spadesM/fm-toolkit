import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

# 1. Dump 0x00696800..0x00696f50 (SpecificallyScoutedPersonReference methods before 0x00696f00)
d.dump_fast("SpecificallyScoutedPersonReference GetProperty", 0x00696800, 0x00696f50)

# 2. Check all USYM line numbers and methods in StreamedTable.cs (0x015de910..0x015f2ffe)
print("\n=== 2. All USYM line transitions in StreamedTable.cs ===")
lo, hi = 0, d.sym_count - 1
while lo < hi:
    mid = (lo + hi) // 2
    rva = struct.unpack_from("<I", d.udata, d.records_off + mid * 24)[0]
    if rva < 0x015de910: lo = mid + 1
    else: hi = mid

prev_line = -1
for idx in range(max(0, lo - 2), d.sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", d.udata, d.records_off + idx * 24)
    if rva > 0x015f3000: break
    fn = d.get_ustr(file_off).split("/")[-1].split("\\")[-1]
    if fn == "StreamedTable.cs" and abs(line - prev_line) > 3:
        print(f"  0x{rva:08x} StreamedTable.cs:{line}")
        prev_line = line
