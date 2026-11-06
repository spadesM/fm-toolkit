import struct
from annotate_sorting_usym import dump_annotated, pe, meta, hdr, rva_to_method_name, rva_to_end, image_base, va_to_off, types_off, methods_off, get_mstr

print("=== 1. Scan all E8/E9 calls to set_DisableSorting (0x015f2420) across GameAssembly.dll ===")
e_lfanew = struct.unpack_from('<I', pe, 0x3C)[0]
num_sections = struct.unpack_from('<H', pe, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from('<H', pe, e_lfanew + 20)[0]
sec_off = e_lfanew + 24 + opt_hdr_size
for i in range(num_sections):
    name = pe[sec_off + i*40 : sec_off + i*40 + 8].rstrip(b'\x00').decode('ascii', errors='ignore')
    vsize, rva, rawsize, rawoff = struct.unpack_from('<IIII', pe, sec_off + i*40 + 8)
    if name == '.text':
        text_rva, text_vsize, text_rawoff = rva, vsize, rawoff
        break

import bisect
sorted_rvas = sorted(rva_to_method_name.keys())
def find_enclosing_method(rva):
    idx = bisect.bisect_right(sorted_rvas, rva) - 1
    if idx >= 0:
        srva = sorted_rvas[idx]
        return f"{rva_to_method_name[srva][0]} (0x{srva:08x}+0x{rva-srva:x})"
    return "unknown"

target_rva = 0x015f2420
for pos in range(text_rawoff, text_rawoff + text_vsize - 5):
    b = pe[pos]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from('<i', pe, pos + 1)[0]
        cur_rva = text_rva + (pos - text_rawoff)
        if cur_rva + 5 + rel == target_rva:
            print(f"  Call to set_DisableSorting at RVA 0x{cur_rva:08x} in {find_enclosing_method(cur_rva)}")

print("\n=== 2. Scan all methods in StreamedTable (TypeDef 5967) for +0x940 (m_initFunction) or +0x9b8 (m_disableSorting) ===")
for rva, names in sorted(rva_to_method_name.items()):
    if any("StreamedTable." in n for n in names):
        sz = rva_to_end.get(rva, rva + 256) - rva
        off = va_to_off(image_base + rva)
        code = pe[off : off + sz]
        if b"\x40\x09\x00\x00" in code:
            print(f"  +0x940 (m_initFunction) referenced in {names[0]} (0x{rva:08x})")
        if b"\xb8\x09\x00\x00" in code:
            print(f"  +0x9b8 (m_disableSorting) referenced in {names[0]} (0x{rva:08x})")

for name, rva in [
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.RecreateHeaders", 0x015eecb0),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedTable.OnBindItem", 0x015eb760),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580),
]:
    dump_annotated(name, rva)
