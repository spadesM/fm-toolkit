import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# 1. Search for b8 4b 63 46 66 c3 (mov eax, 0x6646634b; ret)
func_starts = sorted(rva_to_end.keys())
for label, fourcc in [
    ("0x6646634b (fFcK)", 0x6646634b),
    ("0x41347977 (A4yw - ScoutPlayerPriorities)", 0x41347977),
    ("0x7443314a (tC1J - SpecificallyScoutedPerson)", 0x7443314a),
    ("0x72692047 (ri G)", 0x72692047),
    ("0x736a3232 (sj22)", 0x736a3232),
    ("0x73735043 (ssPC)", 0x73735043),
    ("0x75446333 (uDc3)", 0x75446333),
    ("0x71754c76 (quLv)", 0x71754c76),
    ("0x73714e20 (sqN )", 0x73714e20),
    ("0x6e475773 (nGWs)", 0x6e475773),
]:
    pat = struct.pack("<I", fourcc)
    print(f"=== Search {label} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        pos = idx + 1
        va = off_to_va(idx)
        rva = va - image_base if va else 0
        fidx = bisect.bisect_right(func_starts, rva) - 1
        fn_start = func_starts[fidx] if fidx >= 0 and rva < rva_to_end.get(func_starts[fidx], 0) else 0
        fn_names = rva_to_method_name.get(fn_start, [f"sub_{fn_start:08x}"]) if fn_start else ["data"]
        print(f"  RVA=0x{rva:08x} in {fn_names[0]} (0x{fn_start:08x})")
