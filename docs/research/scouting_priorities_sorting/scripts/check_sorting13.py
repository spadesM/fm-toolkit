import struct, sys
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name, modules, images_off, images_sz

with open("sorting_disasm13.txt", "w", encoding="utf-8") as f:
    sys.stdout = f

    # Find UiRecordID and base classes of SpecificallyScoutedPersonReference
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
            if tname in ("SpecificallyScoutedPersonReference", "ScoutTeamPrioritiesReference", "PlayerReference") or "UiRecordID" in tname or "Polymorphic" in tname or "ManagedObject" in tname:
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"\n=== {iname} Type {ti}: {tname} (tu={tu[:10]}) ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

    # Also list all methods of StreamedTable (Type 5967)
    for img_i in range(images_sz // 40):
        iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
        iname = get_mstr(iu[0])
        if iname == "SI.Bindable.dll":
            t_start, t_cnt = iu[2], iu[3]
            _, m_cnt_mod, m_ptrs_va = modules[iname]
            ptrs_off = va_to_off(m_ptrs_va)
            for ti in range(t_start, t_start + t_cnt):
                tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
                tname = get_mstr(tu[0])
                if tname == "StreamedTable":
                    m_start = tu[9]
                    m_cnt = tu[16] & 0xFFFF
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
        ("StreamedListView.GetItemFromView", 0x015a5a10),
        ("StreamedListView.GetItemFromSource", 0x015a59e0),
        ("StreamedListView.ViewIndexOf", 0x015abba0),
        ("StreamedListView.SourceIndexOf", 0x015a9c50),
        ("StreamedListView.OnBindItemInternal", 0x015a67d0),
        ("StreamedListView.OnRebindItemInternal", 0x015a7660),
        ("StreamedListView.OnUnbindItemInternal", 0x015a8110),
        ("StreamedListView.RefreshInternal", 0x015a9060),
        ("StreamedListView.Rebuild", 0x015a8eb0),
        ("StreamedListView.BindToData", 0x015a49b0),
        ("StreamedListView.SetList", 0x015a9880),
        ("StreamedListView.PostSortingDataChanged", 0x015a8610),
        ("StreamedListView.OnMoveItemInternal", 0x015a7480),
    ]
    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x400)
        dump_fast(name, rva, min(end_rva, rva + 0x1000))
