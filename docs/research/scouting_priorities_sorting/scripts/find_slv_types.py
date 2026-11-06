import struct
from check_header_all_methods import pe, meta, image_base, va_to_off, off_to_va, get_mstr, methods_off, types_off, images_off, images_sz, methods_sz, types_sz

s_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
m_off = pe.find(struct.pack("<Q", off_to_va(s_off)))
_, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, m_off)
ptrs_off = va_to_off(m_ptrs_va)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    if get_mstr(iu[0]) == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname == "StreamedListView":
                print(f"Found StreamedListView at ti={ti}")
                for sub_ti in range(ti - 15, ti + 15):
                    stu = struct.unpack_from("<22i", meta, types_off + sub_ti * 88)
                    stname = get_mstr(stu[0])
                    m_start = stu[9]
                    m_cnt = stu[16] & 0xFFFF
                    print(f"=== Type {sub_ti}: {stname} (methods={m_cnt}) ===")
                    for mi in range(m_start, m_start + m_cnt):
                        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                        mname = get_mstr(mu[0])
                        rid = (mu[6] & 0xFFFFFF) - 1
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                        rva = va - image_base if va else 0
                        print(f"  Method {mi} ({mname}): RVA=0x{rva:08x}")
