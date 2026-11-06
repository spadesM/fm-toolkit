import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, images_off, images_sz, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# Find the type that owns Record..ctor (0x01652750) and RecordSerialisation
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in modules:
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        nspace = get_mstr(tu[1])
        if tname in ("Record", "RecordSerialisation") or "Record" in tname and "SI." in nspace:
            print(f"\n=== Image {iname} | Type {ti}: {nspace}.{tname} (parent={tu[4]}, methods={tu[16]&0xFFFF}) ===")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (0 <= rid < m_cnt_mod and ptrs_off >= 0) else 0
                rva = va - image_base if va else 0
                print(f"  [{mi}] {mname} (slot={mu[9]}, RVA=0x{rva:08x})")
                if tname == "Record" or mname in ("ReadRecordInternal", "ReadTypedListInternal", "ReadTypedValueInternal"):
                    dump_func_details(f"{tname}.{mname}", rva)
                    dump_annotated(f"{tname}.{mname}", rva)
