import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

pe = dhf.pe
meta = dhf.meta
hdr = dhf.hdr
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]

def off_to_va(off):
    for _, vaddr, _, raddr, rsize in dhf.sections:
        if raddr <= off < raddr + rsize:
            return dhf.image_base + vaddr + (off - raddr)
    return 0

si_str_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
si_mod_off = pe.find(struct.pack("<Q", off_to_va(si_str_off)))
_, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, si_mod_off)
ptrs_off = dhf.va_to_off(m_ptrs_va)

for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = dhf.get_mstr(tu[0])
    if tname in ("StreamedListView", "StreamedTable", "VirtualisedList"):
        print(f"=== {tname} (td={ti}) ===")
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = dhf.get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
            rva = va - dhf.image_base if va else 0
            if any(k in mname.lower() for k in ("sort", "order", "reorder", "drag", "header", "column", "bind", "source", "item")):
                print(f"  {mname} (rid={rid}): 0x{rva:08x}")
