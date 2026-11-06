import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

dhf.dump_fast("0x015a9780 (StreamedListView.cs:1207)", 0x015a9780, cds.rva_to_end.get(0x015a9780, 0x015a9900))

# Also find all methods in StreamedListView / StreamedTable that access +0x760 (m_pendingStateChanges) or +0x738 (m_sorting)
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

for name, pat in [("+0x760", b"\x60\x07\x00\x00"), ("+0x738", b"\x38\x07\x00\x00")]:
    print(f"\n=== Hits for {name} ===")
    pos = 0
    seen = set()
    while True:
        idx = code.find(pat, pos)
        if idx == -1:
            break
        rva = start_rva + idx
        b, e, names = find_func(rva)
        if b not in seen:
            seen.add(b)
            print(f"  0x{b:08x}..0x{e:08x}: {names}")
        pos = idx + 1
