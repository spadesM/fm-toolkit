import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, image_base, dump_func_details
)

_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)
tu = struct.unpack_from("<22i", meta, types_off + 5951 * 88)
m_start, m_cnt = tu[9], tu[16] & 0xFFFF
for mi in range(m_start, m_start + m_cnt):
    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
    mname = get_mstr(mu[0])
    rid = (mu[6] & 0xFFFFFF) - 1
    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
    rva = va - image_base if va else 0
    print(f"Header.{mname}: RVA=0x{rva:08x}")
    if rva:
        dump_func_details(f"Header.{mname}", rva)
