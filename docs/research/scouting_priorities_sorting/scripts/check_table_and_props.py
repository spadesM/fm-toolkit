import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, pe, va_to_off, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end

for name, rva in [
    ("StreamedTable.get_DisableSorting", 0x015f2190),
    ("StreamedTable.set_DisableSorting", 0x015f2420),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
]:
    dump_func_details(name, rva)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules: continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if "SpecificallyScoutedPersonReference" in tname or "ScoutingCentreEntryItemReference" in tname:
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"\n=== [{iname}] {tname} methods ===")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
                if rva and sz < 600:
                    dump_func_details(f"{tname}.{mname}", rva)
