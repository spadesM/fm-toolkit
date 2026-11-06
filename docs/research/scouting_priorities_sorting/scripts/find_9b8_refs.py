import sys, bisect
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, image_base, rva_to_method_name, va_to_off

start_rva = 0x01590000
end_rva = 0x015f5000
buf = pe[va_to_off(image_base + start_rva):va_to_off(image_base + end_rva)]
sorted_rvas = sorted(rva_to_method_name.keys())

def find_func(rva):
    idx = bisect.bisect_right(sorted_rvas, rva) - 1
    if idx >= 0:
        frva = sorted_rvas[idx]
        return frva, rva_to_method_name[frva]
    return 0, []

for pat_name, pat in [("0x9b8 (m_DisableSorting)", b"\xb8\x09\x00\x00"), ("0x9b0 (m_SortedColumn)", b"\xb0\x09\x00\x00"), ("0x958 (m_DragCellID)", b"\x58\x09\x00\x00")]:
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
