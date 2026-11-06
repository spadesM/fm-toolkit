import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, images_off, images_sz, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

_, m_cnt_mod, m_ptrs_va = modules["FM.UI.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for ti in (1106, 1534, 413):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
        rva = va - image_base if va else 0
        print(f"{tname}.{mname}: RVA=0x{rva:08x}")
        if tname == "InteropDataHandler" or mname == "TryCreate":
            sz = min(rva_to_end.get(rva, rva + 256) - rva, 512)
            dump_func_details(f"{tname}.{mname}", rva, sz)
            dump_annotated(f"{tname}.{mname}", rva, sz)
