import struct
from check_header_all_methods import pe, meta, image_base, va_to_off, off_to_va, get_mstr, methods_off, types_off, images_off, images_sz, methods_sz, types_sz

# 1. Dump MethodDef 48974 (Header.<>c__DisplayClass36_0.<.ctor>b__0) and all methods of type 5950
tu = struct.unpack_from("<22i", meta, types_off + 5950 * 88)
print("Type 5950:", get_mstr(tu[0]), "methods:", tu[9], tu[16] & 0xFFFF)

# Find SI.Bindable.dll module ptrs
s_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
m_off = pe.find(struct.pack("<Q", off_to_va(s_off)))
_, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, m_off)
ptrs_off = va_to_off(m_ptrs_va)

for ti in range(5945, 5970):
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
        print(f"  Method {mi} ({mname}): RVA=0x{rva:08x}")
