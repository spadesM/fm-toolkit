import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, image_base, rva_to_method_name, dump_func_details, va_to_off

start_rva = 0x01590000
end_rva = 0x015f5000
off_start = va_to_off(image_base + start_rva)
off_end = va_to_off(image_base + end_rva)
buf = pe[off_start:off_end]

sorted_rvas = sorted(rva_to_method_name.keys())
import bisect

def find_func(rva):
    idx = bisect.bisect_right(sorted_rvas, rva) - 1
    if idx >= 0:
        frva = sorted_rvas[idx]
        return frva, rva_to_method_name[frva]
    return 0, []

for pat_name, pat in [("0x5c1", b"\xc1\x05\x00\x00"), ("0x5c0", b"\xc0\x05\x00\x00"), ("0x778", b"\x78\x07\x00\x00"), ("0x7b0 (m_DisableSorting)", b"\xb0\x07\x00\x00")]:
    print(f"=== Pattern {pat_name} ===")
    pos = 0
    while True:
        idx = buf.find(pat, pos)
        if idx == -1:
            break
        rva = start_rva + idx
        frva, names = find_func(rva)
        print(f"  RVA 0x{rva:08x} in 0x{frva:08x} (+0x{rva-frva:03x}): {names}")
        pos = idx + 1
