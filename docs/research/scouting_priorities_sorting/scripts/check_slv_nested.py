import struct
from fast_disasm_key_spots import dump_func, meta, pe, image_base, va_to_off, off_to_va, get_mstr, methods_off, types_off

dump_func("Header.<>c__DisplayClass36_0.<.ctor>b__0", 0x015f2ea0, 420)
dump_func("Header.UpdateSortingIcons", 0x015df970, 176)

# Also list nested types around StreamedListView
s_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
m_off = pe.find(struct.pack("<Q", off_to_va(s_off)))
_, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, m_off)
ptrs_off = va_to_off(m_ptrs_va)

for ti in range(5880, 5945):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if any(k in tname for k in ("StreamedListView", "Sort", "DisplayClass", "<>c")):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"=== Type {ti}: {tname} ===")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            if "Sort" in mname or "b__" in mname or "Compare" in mname or "Setup" in mname or "Reorder" in mname or "StateChanged" in mname:
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x}")
