import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, dump_func_details, rva_to_end

str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
types_off, types_sz = hdr[40], hdr[41]
str_off, str_sz = hdr[6], hdr[7]

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

# 1. File offset 0x004628d0 -> RVA = off_to_va(0x004628d0) - image_base
rva_j1ct = off_to_va(0x004628d0) - image_base
print(f"File offset 0x004628d0 is RVA 0x{rva_j1ct:08x}")
dump_with_strings("J1Ct PropertyRegistration", rva_j1ct - 0x20, 0x380)

# 2. Also find ao3d (0x64336f61 / 0x616f3364) in pe
for pat, name in [(b"J1Ct", "J1Ct_fwd"), (b"tC1J", "J1Ct_rev"), (b"ao3d", "ao3d_fwd"), (b"d3oa", "ao3d_rev")]:
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003e4f30 <= rva <= 0x004c5d06:
            print(f"Found {name} at file off 0x{idx:x}, RVA 0x{rva:08x}")
            dump_with_strings(f"{name}_reg", rva - 0x20, 0x380)
        pos = idx + 1

# 3. Dump Bindings.GetNthProperty (0x014c1450)
dump_with_strings("Bindings.GetNthProperty", 0x014c1450, 0x100)
