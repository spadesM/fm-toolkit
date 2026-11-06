import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, dump_func_details, rva_to_end

str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]

def get_str_literal(idx: int) -> str:
    if idx < 0 or idx * 8 >= str_lit_sz:
        return f"<oob:{idx}>"
    length, data_idx = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    raw = meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length]
    return raw.decode("utf-8", errors="replace")

def resolve_data_rva(rva: int) -> str:
    off = va_to_off(image_base + rva)
    if off < 0 or off + 8 > len(pe):
        return ""
    val = struct.unpack_from("<Q", pe, off)[0]
    tag = val >> 29
    idx = (val & 0x1FFFFFFF) >> 1
    if tag == 5:
        return f"str_lit[{idx}] = {get_str_literal(idx)!r}"
    elif tag in (1, 2, 3, 4, 6):
        return f"meta_usage(tag={tag}, idx={idx})"
    return ""

def dump_with_strings(label, rva, sz=None):
    if sz is None:
        sz = rva_to_end.get(rva, rva + 256) - rva
    dump_func_details(label, rva, sz)
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    print("  --- RIP Data Annotations ---")
    for i in range(len(code) - 7):
        if code[i] in (0x48, 0x4c) and code[i+1] in (0x8b, 0x8d) and (code[i+2] & 0xc7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            trva = rva + i + 7 + disp
            info = resolve_data_rva(trva)
            if info:
                print(f"  +0x{i:03x}: RIP -> 0x{trva:08x} ({info})")

# 1. Actual J1Ct registration starting around RVA 0x004642c0
dump_with_strings("J1Ct Actual Registration", 0x004642c0, 0x480)

# 2. StreamedTable key methods
targets = [
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 494),
    ("StreamedTable.CreateColumns", 0x015e83b0, 2883),
    ("StreamedTable.CreateColumn", 0x015e7dc0, 942),
    ("StreamedTable.CreateHeader", 0x015e8f00, 421),
    ("StreamedTable.BindHeader", 0x015e6230, 2659),
    ("StreamedTable.RefreshInternal", 0x015eed80, 450),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640, 713),
    ("StreamedTable.OnBindItem", 0x015eb760, 922),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580, 630),
    ("StreamedTable.OnRebindItem", 0x015ed7d0, 761),
]

for label, rva, sz in targets:
    dump_with_strings(label, rva, sz)
