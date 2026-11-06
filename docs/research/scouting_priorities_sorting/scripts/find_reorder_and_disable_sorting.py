import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, dump_func_details, rva_to_method_name, va_to_off, image_base, types_off, types_sz, methods_off, get_mstr, meta

print("0x015a5680 name:", rva_to_method_name.get(0x015a5680))
for k in range(0x015a5600, 0x015a5700, 0x10):
    if k in rva_to_method_name:
        print(f"  0x{k:08x}: {rva_to_method_name[k]}")
dump_func_details("Func_0x015a5640", 0x015a5640, 0x100)

# Scan StreamedListView (0x015a3000..0x015b3000) and StreamedTable (0x015df000..0x01610000) for offset 0x68c and 0x9b8
for label, start_rva, end_rva in [("StreamedListView", 0x015a3000, 0x015b3000), ("StreamedTable", 0x015df000, 0x01610000)]:
    off_s = va_to_off(image_base + start_rva)
    off_e = va_to_off(image_base + end_rva)
    chunk = pe[off_s:off_e]
    for pat_name, pat in [("0x68c", b"\x8c\x06\x00\x00"), ("0x9b8", b"\xb8\x09\x00\x00"), ("0x9b9", b"\xb9\x09\x00\x00")]:
        idx = 0
        while True:
            idx = chunk.find(pat, idx)
            if idx == -1:
                break
            rva = start_rva + idx
            fn_rva = max((k for k in rva_to_method_name if k <= rva), default=0)
            print(f"[{label}] {pat_name} at RVA 0x{rva:08x} in {rva_to_method_name.get(fn_rva, [hex(fn_rva)])} (+0x{rva-fn_rva:x})")
            idx += 1
