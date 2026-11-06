import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va,
    dump_func_details, rva_to_end, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules
)

# 1. Print vtable slots 190..235 of StreamedListView and StreamedTable
_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for tid, tname in [(5791, "StreamedListView"), (5967, "StreamedTable")]:
    tu = struct.unpack_from("<22i", meta, types_off + tid * 88)
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n=== Virtual Methods of {tname} ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        slot = mu[9]
        if slot != 65535:
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
            rva = va - image_base if va else 0
            print(f"  slot {slot} (offset 0x{0x138 + slot*16:x}): {mname} RVA=0x{rva:08x}")

# 2. Find ScoutPlayerPrioritiesReference and related types across all images
print("\n=== Searching for Scout / SpecificallyScouted types ===")
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in modules:
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_img, m_ptrs_va_img = modules[iname]
    ptrs_off_img = va_to_off(m_ptrs_va_img)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if "Scout" in tname and ("Priorit" in tname or "Specific" in tname or "Reference" in tname):
            print(f"Type {ti} ({iname}): {tname}")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off_img + rid * 8)[0] if 0 <= rid < m_cnt_img else 0
                rva = va - image_base if va else 0
                print(f"    Method {mi} ({mname}): RVA=0x{rva:08x}")
