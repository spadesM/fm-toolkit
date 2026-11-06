import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

# Search 0x01590000..0x01630000 for:
# - CALL to 0x015f2230 (get_IsDragCellActive)
# - offset 0x958 (m_dragCellID)
# - offset 0x9da (m_disableSorting)
# - offset 0x5c1 (m_reorderable)
pe = cds.pe
start_rva = 0x01590000
end_rva = 0x01630000
start_off = cds.va_to_off(cds.image_base + start_rva)
end_off = cds.va_to_off(cds.image_base + end_rva)
code = pe[start_off:end_off]

def find_func(rva):
    for b_rva, e_rva in cds.rva_to_end.items():
        if b_rva <= rva < e_rva:
            return b_rva, e_rva, cds.rva_to_method_name.get(b_rva, [])
    return 0, 0, []

for pat_name, pat_bytes in [
    ("+0x958 (m_dragCellID)", b"\x58\x09\x00\x00"),
    ("+0x9da (m_disableSorting)", b"\xda\x09\x00\x00"),
    ("+0x5c1 (m_reorderable)", b"\xc1\x05\x00\x00"),
]:
    print(f"\n=== Hits for {pat_name} ===")
    pos = 0
    while True:
        idx = code.find(pat_bytes, pos)
        if idx == -1:
            break
        rva = start_rva + idx
        b, e, names = find_func(rva)
        print(f"  RVA 0x{rva:08x} in 0x{b:08x} ({', '.join(names[:3])})")
        pos = idx + 1

print("\n=== Calls to 0x015f2230 (get_IsDragCellActive) ===")
for i in range(len(code) - 5):
    if code[i] in (0xE8, 0xE9):
        disp = struct.unpack_from("<i", code, i + 1)[0]
        target = start_rva + i + 5 + disp
        if target == 0x015f2230:
            rva = start_rva + i
            b, e, names = find_func(rva)
            print(f"  RVA 0x{rva:08x} in 0x{b:08x} ({', '.join(names[:3])})")
