import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, dump_func_details, rva_to_end

str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
str_off, str_sz = hdr[6], hdr[7]
types_off, types_sz = hdr[40], hdr[41]
methods_off, methods_sz = hdr[32], hdr[33]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

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

# Scan .text in the big registration function (0x003e4f30 .. 0x004c5d06) for references to 0x02e1a690 and 0x02de2548
reg_start_off = va_to_off(image_base + 0x003e4f30)
reg_end_off = va_to_off(image_base + 0x004c5d06)
code = pe[reg_start_off:reg_end_off]

for i in range(len(code) - 7):
    if code[i] in (0x48, 0x4c) and code[i+1] in (0x8b, 0x8d) and (code[i+2] & 0xc7) == 0x05:
        disp = struct.unpack_from("<i", code, i + 3)[0]
        cur_rva = 0x003e4f30 + i
        trva = cur_rva + 7 + disp
        if trva in (0x02e1a690, 0x02de2548):
            print(f"Found ref to 0x{trva:08x} at RVA 0x{cur_rva:08x}")
            dump_with_strings(f"Ref_0x{trva:08x}", cur_rva - 0x100, 0x400)
