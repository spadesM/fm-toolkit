import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

pe = cds.pe
start_rva = 0x01580000
end_rva = 0x01700000
start_off = cds.va_to_off(cds.image_base + start_rva)
end_off = cds.va_to_off(cds.image_base + end_rva)
code = pe[start_off:end_off]

def find_func(rva):
    for b_rva, e_rva in cds.rva_to_end.items():
        if b_rva <= rva < e_rva:
            return b_rva, e_rva, cds.rva_to_method_name.get(b_rva, [])
    return 0, 0, []

pat_bytes = b"\xb8\x09\x00\x00"
print("=== Hits for +0x9b8 (m_disableSorting) ===")
pos = 0
funcs_to_dump = []
while True:
    idx = code.find(pat_bytes, pos)
    if idx == -1:
        break
    rva = start_rva + idx
    b, e, names = find_func(rva)
    print(f"  RVA 0x{rva:08x} in 0x{b:08x}..0x{e:08x} ({', '.join(names[:3])}) bytes={code[idx-4:idx+6].hex(' ')}")
    if b and (b, e, names) not in funcs_to_dump:
        funcs_to_dump.append((b, e, names))
    pos = idx + 1

for b, e, names in funcs_to_dump:
    dhf.dump_fast(f"{', '.join(names[:2])}", b, e)
