import struct
from check_header_all_methods import pe, meta, image_base, va_to_off, get_mstr, methods_off, types_off, methods_sz, types_sz

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
lit_cnt = str_lit_sz // 8
literals = [
    meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length].decode("utf-8", errors="replace")
    for length, data_idx in (struct.unpack_from("<II", meta, str_lit_off + i * 8) for i in range(lit_cnt))
]

def resolve_rip_va(va: int) -> str:
    foff = va_to_off(va)
    if foff < 0 or foff + 8 > len(pe):
        return ""
    val = struct.unpack_from("<I", pe, foff)[0]
    if (val & 1) == 1:
        tag = val >> 29
        idx = (val & 0x1FFFFFFF) >> 1
        if tag == 5 and 0 <= idx < len(literals):
            return f'STR "{literals[idx]}"'
        elif tag == 3 and 0 <= idx * 36 < methods_sz:
            mu = struct.unpack_from("<7i4H", meta, methods_off + idx * 36)
            if 0 <= mu[1] * 88 < types_sz:
                tu = struct.unpack_from("<22i", meta, types_off + mu[1] * 88)
                return f"MethodDef {get_mstr(tu[0])}.{get_mstr(mu[0])}"
        return f"MetaUsage(tag={tag}, idx={idx})"
    return ""

def dump_clean(label, rva, sz):
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for line_off in range(0, len(code), 16):
        chunk = code[line_off : line_off + 16]
        print(f"  +0x{line_off:03x}: {chunk.hex(' ')}")
    print("  --- Annotations ---")
    for i in range(len(code)):
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            op = "CALL" if code[i] == 0xE8 else "JMP"
            print(f"  +0x{i:03x}: {op} 0x{target_rva:08x}")
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            target_va = image_base + rva + i + 7 + disp
            info = resolve_rip_va(target_va)
            if info:
                print(f"  +0x{i:03x}: RIP [0x{target_va - image_base:08x}] -> {info}")

dump_clean("StreamedTable.OnHeaderClicked", 0x015ec910, 600)
dump_clean("<>c__DisplayClass259_0.<MakeColumnHeader>b__0", 0x0160bb80, 96)
dump_clean("Bindings.Create", 0x014bf980, 400)
dump_clean("Bindings.Bind", 0x014bee30, 200)
dump_clean("StreamedTable.OnRebindItem", 0x015ed7d0, 768)
dump_clean("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 500)
