import struct, sys, bisect
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out = open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\reorderable_refs.txt", "w", encoding="utf-8")
sys.stdout = out
from check_deep_sorting import pe, va_to_off, image_base, rva_to_end, rva_to_method_name, dump_func_details
sorted_rvas = sorted(rva_to_method_name.keys())
def owner(rva):
    i = bisect.bisect_right(sorted_rvas, rva) - 1
    s = sorted_rvas[i]
    return s, rva_to_method_name[s]

dump_func_details("StreamedListView.set_Reorderable", 0x15ad4f0)
# getter for StreamedListView.Reorderable?
for r, ns in sorted(rva_to_method_name.items()):
    for n in ns:
        if n.startswith("StreamedListView.get_") or n.startswith("StreamedListView.set_"):
            print(hex(r), n, pe[va_to_off(image_base+r):va_to_off(image_base+r)+16].hex(" "))

lo, hi = 0x14d0000, 0x1620000
so, eo = va_to_off(image_base + lo), va_to_off(image_base + hi)
for disp in (0x5c1, 0x778):
    pat = struct.pack("<I", disp)
    print(f"\n===== disp {hex(disp)} =====")
    pos = so
    while True:
        idx = pe.find(pat, pos, eo)
        if idx == -1: break
        rva = lo + (idx - so)
        s, names = owner(rva)
        print(f"  {hex(rva)} in {hex(s)} {names[:2]} ctx={pe[idx-4:idx+6].hex(' ')}")
        pos = idx + 1
out.close()
