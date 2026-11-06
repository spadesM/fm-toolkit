import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va, get_mstr,
    types_off, types_sz, fields_off, fields_sz, methods_off, methods_sz,
    images_off, images_sz, modules
)
from parse_st_data_exact import get_ref_bytes

# Find all types in SI.Bindable.dll and SI.UI.dll that have methods around 0x015f36b0, 0x015b0b50, etc.
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in ("SI.Bindable.dll", "SI.UI.dll"):
        continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    t_start, t_cnt = iu[2], iu[3]
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname == "UxmlSerializedData":
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            rvas = []
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                rvas.append((get_mstr(mu[0]), rva))
            # Check if any rva matches or if f_cnt is large
            f_start = tu[8]
            f_cnt = tu[17] & 0xFFFF
            if any(rva in (0x015f36b0, 0x015b0b50) for _, rva in rvas) or f_cnt >= 30:
                print(f"\n=== Type[{ti}] in {iname}: {tname} (fields={f_cnt}, methods={rvas}) ===")
                for fi in range(f_start, f_start + f_cnt):
                    fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                    print(f"  Field[{fi - f_start:2d}]: {get_mstr(fu[0])} (type_byval={fu[1]})")
