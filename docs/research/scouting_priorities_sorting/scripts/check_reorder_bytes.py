import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from scan_table_methods import pe, meta, types_off, methods_off, images_off, images_sz, get_mstr, ptrs_off, m_cnt_mod, image_base, rva_to_end, va_to_off

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    if get_mstr(iu[0]) == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("StreamedListView", "StreamedTable"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    if "Reorder" in mname or "Drag" in mname:
                        rid = (mu[6] & 0xFFFFFF) - 1
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                        rva = va - image_base
                        foff = va_to_off(va)
                        print(f"{tname}.{mname} RVA=0x{rva:08x}: {pe[foff:foff+32].hex(' ')}")
