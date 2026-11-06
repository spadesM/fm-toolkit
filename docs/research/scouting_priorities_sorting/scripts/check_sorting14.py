import struct, sys
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name, modules, images_off, images_sz

with open("sorting_disasm14.txt", "w", encoding="utf-8") as f:
    sys.stdout = f

    # Find types with GetPropertyTypeInternal or TryGetProperty or GetProperty
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
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            mnames = [get_mstr(struct.unpack_from("<7i4H", meta, methods_off + mi * 36)[0]) for mi in range(m_start, m_start + m_cnt)]
            if any(x in mnames for x in ("GetPropertyTypeInternal", "TryGetProperty", "TryGetPropertyInternal")) or tname == "UiRecordID":
                if "Reference" in tname and tname not in ("SpecificallyScoutedPersonReference", "ScoutTeamPrioritiesReference", "PlayerReference", "PersonReference"):
                    continue
                print(f"\n=== {iname} Type {ti}: {tname} (methods={m_cnt}) ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

    targets = [
        ("StreamedTable.OnBindItem", 0x015eb760),
        ("StreamedTable.OnRebindItem", 0x015ed7d0),
        ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580),
        ("StreamedTable.OnMakeItem", 0x015ecc60),
    ]
    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x400)
        dump_fast(name, rva, min(end_rva, rva + 0x1000))
