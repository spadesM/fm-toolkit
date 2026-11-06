import struct, sys
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name, modules, images_off, images_sz

with open("sorting_disasm12.txt", "w", encoding="utf-8") as f:
    sys.stdout = f

    # 1. Dump 0x002ae590 (AutogenBindings) and see how it resolves 4-byte IDs to strings
    end_2ae = rva_to_end.get(0x002ae590, 0x002ae590 + 0x400)
    dump_fast("AutogenBindings_0x002ae590", 0x002ae590, min(end_2ae, 0x002ae590 + 0x800))

    # 2. List all methods of StreamedListView (Type 5791) and VirtualisedList
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
            if tname in (
                "StreamedListView",
                "VirtualisedList",
                "SpecificallyScoutedPersonReference",
                "ScoutTeamPrioritiesReference",
                "ManagedObjectReference",
                "PolymorphicManagedObjectReference",
            ):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                parent_idx = tu[3]
                print(f"\n=== {iname} Type {ti}: {tname} (parent={parent_idx}, methods={m_cnt}) ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
                    # Check if method body references offset 0x568 (m_indices) or 0x5c1 (m_reorderable) or 0x9b8 (DisableSorting)
                    if rva > 0 and sz > 0:
                        off = va_to_off(image_base + rva)
                        code = pe[off : off + sz]
                        hits = []
                        if b"\x68\x05\x00\x00" in code:
                            hits.append("+0x568(m_indices)")
                        if b"\xc1\x05\x00\x00" in code:
                            hits.append("+0x5c1(m_reorderable?)")
                        if b"\xb8\x09\x00\x00" in code:
                            hits.append("+0x9b8(DisableSorting)")
                        if b"\x38\x07\x00\x00" in code:
                            hits.append("+0x738(m_sortings)")
                        if b"\x88\x07\x00\x00" in code:
                            hits.append("+0x788(SortBinding)")
                        if hits:
                            print(f"    -> REFS: {', '.join(hits)}")
