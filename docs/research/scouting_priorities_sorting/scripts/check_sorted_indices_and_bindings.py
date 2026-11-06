import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
import check_deep_sorting as cds
import struct

# 1. Find all references to +0x568 (68 05 00 00) in StreamedListView / StreamedTable (0x01590000 .. 0x01620000)
start_rva = 0x01590000
end_rva = 0x01620000
off_start = cds.va_to_off(cds.image_base + start_rva)
off_end = cds.va_to_off(cds.image_base + end_rva)
chunk = cds.pe[off_start:off_end]

for pat_name, pat in [("+0x568 (m_sortedIndices)", b"\x68\x05\x00\x00"), ("+0x5d0 (m_sortComparer)", b"\xd0\x05\x00\x00"), ("+0x5d8 (m_sortData)", b"\xd8\x05\x00\x00"), ("+0x600", b"\x00\x06\x00\x00"), ("+0x604", b"\x04\x06\x00\x00")]:
    print(f"=== References to {pat_name} ===")
    idx = 0
    while True:
        pos = chunk.find(pat, idx)
        if pos == -1:
            break
        rva = start_rva + pos
        # find containing method
        m_rva = None
        for cand in range(rva, rva - 0x2000, -1):
            if cand in cds.rva_to_method_name:
                m_rva = cand
                break
        m_name = cds.rva_to_method_name.get(m_rva, f"0x{m_rva:08x}" if m_rva else "unknown")
        print(f"  0x{rva:08x} in {m_name} (0x{m_rva:08x}+0x{rva-m_rva:x})" if m_rva else f"  0x{rva:08x}")
        idx = pos + 1

# 2. Disassemble 0x014bf980, 0x014c3050, 0x014bee30, and callback in BindSortPathNextDepth
for label, s_rva in [
    ("Bindings_0x014bf980", 0x014bf980),
    ("Bindings_0x014c3050", 0x014c3050),
    ("Bindings_0x014bee30", 0x014bee30),
]:
    e_rva = cds.rva_to_end.get(s_rva, s_rva + 0x300)
    dhf.dump_fast(label, s_rva, e_rva)
