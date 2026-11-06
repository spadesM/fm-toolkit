import struct
from check_deep_sorting import meta, pe, types_off, types_sz, methods_off, images_off, images_sz, get_mstr, modules, va_to_off, image_base, dump_func_details

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
        decl_ti = tu[3]
        if decl_ti >= 0:
            #decl_ti is a TypeIndex or TypeDefinitionIndex? Wait: let's check adjacent type
            pass
        if tname in ("StreamedTable", "StreamedListView", "VirtualisedList", "Bindings", "Node") or (tname == "UxmlSerializedData" and ti > 0):
            prev_tu = struct.unpack_from("<22i", meta, types_off + (ti - 1) * 88)
            prev_tname = get_mstr(prev_tu[0])
            if tname == "UxmlSerializedData" and prev_tname not in ("StreamedTable", "StreamedListView", "VirtualisedList"):
                continue
            label = f"{prev_tname}/{tname}" if tname == "UxmlSerializedData" else tname
            print(f"\n=== {label} (ti={ti}) ===")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                rva = 0
                if 0 <= rid < m_cnt_mod:
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                    if va > 0:
                        rva = va - image_base
                print(f"  0x{rva:08x}: {label}.{mname}")
