import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, image_base, off_to_va, va_to_off, rva_to_method_name, dump_func_details

patterns = [
    ("J1Ct (0x7443314a)", struct.pack("<I", 0x7443314a)),
    ("dxMa (0x644d7861)", struct.pack("<I", 0x644d7861)),
    ("cYEE (0x63594545)", struct.pack("<I", 0x63594545)),
    ("wy4A (0x41347977)", struct.pack("<I", 0x41347977)),
    ("ssPC (0x73735043)", struct.pack("<I", 0x73735043)),
]

for label, pat in patterns:
    idx = 0
    hits = []
    while True:
        idx = pe.find(pat, idx)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        hits.append(rva)
        idx += 1
    print(f"{label}: {[hex(h) for h in hits]}")
