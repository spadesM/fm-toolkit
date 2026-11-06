import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_vtable import meta, pe, images_off, images_sz, types_off, methods_off, get_mstr, modules, va_to_off, image_base
from check_sorting_details import dump_fast

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname != "SI.Bindable.dll": continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(5935, 5970):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        tns = get_mstr(tu[1])
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\n=== {tns}.{tname} (ti={ti}) ===")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
            rva = (va - image_base) if va > 0 else 0
            slot = mu[10]
            print(f"  [mi={mi}] 0x{rva:08x}: {mname}")
            if mi in (49027, 49029, 49020, 49021, 49022):
                dump_fast(f"{tname}.{mname}", rva, rva + 0x150)
