import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, off_to_va, image_base, root,
    types_off, fields_off, methods_off, get_mstr, rva_to_method_name
)
from dump_headers_fast import dump_fast

print("=== 1. Search for +0x838 (38 08 00 00) in StreamedTable (0x015de000..0x015f6000) ===")
start_off = va_to_off(image_base + 0x015de000)
end_off = va_to_off(image_base + 0x015f6000)
pos = start_off
while True:
    idx = pe.find(b"\x38\x08\x00\x00", pos, end_off)
    if idx == -1:
        break
    rva = off_to_va(idx) - image_base
    print(f"  Found +0x838 at RVA 0x{rva:08x}")
    dump_fast(f"ref_838_{rva:08x}", rva - 0x20, rva + 0x30)
    pos = idx + 1

print("\n=== 2. Check StreamedTableView methods to see field offsets of StreamedTableView ===")
tu = struct.unpack_from("<22i", meta, types_off + 6093 * 88)
m_start = tu[9]
m_cnt = tu[16] & 0xFFFF
for rva in (0x00366b70, 0x002867d0, 0x0028a150, 0x0029bfd0, 0x00285830, 0x00291ab0, 0x00290320, 0x01621d40):
    dump_fast(f"StreamedTableView_method_{rva:08x}", rva, rva + 0x40)
