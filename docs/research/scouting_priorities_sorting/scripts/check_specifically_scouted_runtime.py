import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va,
    dump_func_details, rva_to_end, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules, rva_to_method_name
)

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

sorted_func_rvas = sorted(rva_to_method_name.keys())

def find_containing_func(rva):
    i = bisect.bisect_right(sorted_func_rvas, rva) - 1
    if i >= 0:
        fn_rva = sorted_func_rvas[i]
        end_rva = rva_to_end.get(fn_rva, fn_rva + 0x1000)
        if fn_rva <= rva < end_rva or (rva - fn_rva) < 0x10000:
            return fn_rva, rva_to_method_name[fn_rva]
    return 0, []

fourccs = [
    ("rylp", b"\x72\x79\x6c\x70"),
    ("axMd", b"\x61\x78\x4d\x64"),
    ("EEYc", b"\x45\x45\x59\x63"),
    ("3cDu", b"\x33\x63\x44\x75"),
    ("vLuq", b"\x76\x4c\x75\x71"),
    (" Nqs", b"\x20\x4e\x71\x73"),
    ("sWGn", b"\x73\x57\x47\x6e"),
    ("tC1J (SpecificallyScoutedPerson)", b"\x4a\x31\x43\x74"),
    ("22js (SpecificallyScoutedPlayers)", b"\x32\x32\x6a\x73"),
    ("CPss (SpecificallyScoutedPlayersCount)", b"\x43\x50\x73\x73"),
    ("g96I", b"\x49\x36\x39\x67"),
    ("ri G", b"\x47\x20\x69\x72"),
    ("Ha7v (ScoutPriorities)", b"\x48\x61\x37\x76"),
]

for label, pat in fourccs:
    print(f"\n=== FourCC {label} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            fn_rva, fn_names = find_containing_func(rva)
            if "rylp" not in label or (0x003e0000 <= rva <= 0x00520000) or any("Scout" in n or "Specific" in n or "Priorit" in n for n in fn_names):
                print(f"  RVA 0x{rva:08x} in 0x{fn_rva:08x} {fn_names[:4]}")
                if 0x003e0000 <= rva <= 0x004c5d06:
                    for off_delta in range(-48, 96):
                        cur = idx + off_delta
                        if pe[cur:cur+3] == b"\x4c\x8b\x05":
                            disp = struct.unpack_from("<i", pe, cur + 3)[0]
                            target_rva = (rva + off_delta) + 7 + disp
                            info = resolve_data_rva(target_rva)
                            if "str_lit" in info:
                                print(f"    delta {off_delta:+d}: {info}")
        pos = idx + 1
