import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, rva_to_end, rva_to_method_name, get_mstr, types_off, methods_off
from annotate_sorting_usym import resolve_rip_va, usym_map

def dump_bytes_and_usym(label, rva):
    sz = rva_to_end.get(rva, rva + 256) - rva
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for line_off in range(0, len(code), 16):
        chunk = code[line_off : line_off + 16]
        print(f"  +0x{line_off:03x}: {chunk.hex(' ')}")
    print("  --- Detailed trace ---")
    for i in range(len(code)):
        cur_rva = rva + i
        if cur_rva in usym_map:
            for sym, fn, ln in usym_map[cur_rva]:
                short_fn = fn.split("/")[-1].split("\\")[-1] if fn else ""
                if ln > 0 or sym:
                    print(f"  [USYM +0x{i:03x}] {short_fn}:{ln} ({sym})")
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            names = rva_to_method_name.get(target_rva, [])
            if names or (0x00500000 <= target_rva <= 0x02500000):
                op = "CALL" if code[i] == 0xE8 else "JMP"
                print(f"  +0x{i:03x}: {op} 0x{target_rva:08x} -> {', '.join(names[:4])}")
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            target_va = image_base + rva + i + 7 + disp
            info = resolve_rip_va(target_va)
            if info:
                print(f"  +0x{i:03x}: RIP [0x{target_va - image_base:08x}] -> {info}")

dump_bytes_and_usym("StreamedTable.OnBindItem", 0x015eb760)
dump_bytes_and_usym("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580)
dump_bytes_and_usym("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320)
