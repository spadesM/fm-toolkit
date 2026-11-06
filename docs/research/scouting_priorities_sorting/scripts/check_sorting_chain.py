import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, sections, dump_func_details, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules, rva_to_method_name

str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]

def get_str_literal(idx: int) -> str:
    if idx < 0 or idx * 8 >= str_lit_sz:
        return f"<oob:{idx}>"
    length, data_idx = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    raw = meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length]
    return raw.decode("utf-8", errors="replace")

for rva in (0x02e38980, 0x02e11f78, 0x02e11ea0, 0x02e38690, 0x02e38840, 0x02e38760):
    off = va_to_off(image_base + rva)
    val = struct.unpack_from("<Q", pe, off)[0] if off >= 0 else -1
    print(f"RVA 0x{rva:08x} -> off=0x{off:x}, val=0x{val:016x}")

# Let's print sections to see where 0x02e38980 lives
for s in sections:
    print("Section:", s[0], f"vaddr=0x{s[1]:08x} vsize=0x{s[2]:08x} raddr=0x{s[3]:08x} rsize=0x{s[4]:08x}")

# Let's check what methods are at 0x00abdcc0, 0x00af20c0, 0x00af8a80, and in Header / StreamedListView
for rva in (0x00abdcc0, 0x00af20c0, 0x00af8a80):
    print(f"RVA 0x{rva:08x} names:", rva_to_method_name.get(rva))
    dump_func_details(f"Method_0x{rva:08x}", rva)

# Let's list all methods of StreamedListView and Header in FM.UI.dll / SI.Bindable.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname in ("FM.UI.dll", "SI.Bindable.dll"):
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("StreamedListView", "Header") or "DisplayClass" in tname:
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                # Check if any method is near 0x015dfab0..0x015f4000 or 0x015a3000..0x015ab000
                printed_header = False
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    if tname in ("StreamedListView", "Header") or (0x015df000 <= rva <= 0x015f4000):
                        if not printed_header:
                            print(f"=== {iname} Type {ti}: {tname} ===")
                            printed_header = True
                        print(f"  {mname}: RVA=0x{rva:08x}")
