import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, get_mstr, image_base, va_to_off, rva_to_end,
    images_off, images_sz, types_off, types_sz, methods_off, fields_off, modules,
    rva_to_method_name, dump_func_details
)

# Dump all methods & fields of SortComparer (5783), SortData (5786), Header (5951)
_, m_cnt_mod, m_ptrs_va = modules["FM.UI.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for ti in (5783, 5786, 5951):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    f_start = tu[8]
    f_cnt = tu[17] & 0xFFFF
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n================ Type {ti}: {tname} ================")
    for fi in range(f_start, f_start + f_cnt):
        fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
        print(f"  Field {fi - f_start}: {get_mstr(fu[0])}")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
        rva = va - image_base if va else 0
        sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
        print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
        if rva:
            dump_func_details(f"{tname}.{mname}", rva, sz)
