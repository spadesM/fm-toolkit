import struct, sys, bisect
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out = open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\reorderable_vs_sorting.txt", "w", encoding="utf-8")
sys.stdout = out
from check_deep_sorting import pe, va_to_off, image_base, rva_to_end, rva_to_method_name, dump_func_details

sorted_rvas = sorted(rva_to_method_name.keys())
def owner(rva):
    i = bisect.bisect_right(sorted_rvas, rva) - 1
    s = sorted_rvas[i]
    return s, rva_to_method_name[s]

# scan for disp32 0x68c, 0x9b8, 0x764 in SI.Bindable StreamedListView/Table range
lo, hi = 0x1590000, 0x1620000
so, eo = va_to_off(image_base + lo), va_to_off(image_base + hi)
for disp in (0x68c, 0x9b8, 0x764):
    pat = struct.pack("<I", disp)
    print(f"\n===== disp {hex(disp)} =====")
    pos = so
    while True:
        idx = pe.find(pat, pos, eo)
        if idx == -1:
            break
        rva = lo + (idx - so)
        s, names = owner(rva)
        ctx = pe[idx-4:idx+6].hex(" ")
        print(f"  {hex(rva)} in {hex(s)} {names[:2]} ctx={ctx}")
        pos = idx + 1
out.close()
