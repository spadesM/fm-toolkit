import struct
from check_deep_sorting import (
    pe, image_base, va_to_off, dump_func_details, rva_to_method_name,
    meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end
)

# Find all types around Header (Type 5951..5958)
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            if 5948 <= ti <= 5970:
                tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
                tname = get_mstr(tu[0])
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"=== Type {ti}: {tname} ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
                    if ti in (5952, 5953, 5954) and rva:
                        dump_func_details(f"{tname}.{mname}", rva, sz)
