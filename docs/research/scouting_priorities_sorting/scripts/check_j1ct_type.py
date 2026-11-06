import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import (
    pe, meta, image_base, va_to_off, get_mstr,
    images_off, images_sz, types_off, methods_off, modules, dump_func_details
)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules:
        continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    if ptrs_off < 0 or m_cnt_mod == 0:
        continue
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        ns = get_mstr(tu[1])
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        if any(k in tname for k in ["ScoutPriorit", "SpecificallyScouted"]):
            print(f"[{iname}] {ns}.{tname} (type {ti}):")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                print(f"  {mname}: 0x{rva:08x}")
