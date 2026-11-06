import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, va_to_off, pe, image_base, rva_to_end

dump_func_details("StreamedListView.SetSortingBinding_1", 0x015a9a80)
dump_func_details("StreamedListView.SetSortingBinding_2", 0x015a9ae0)
dump_func_details("StreamedListView.ApplySorting", 0x015a4260)
dump_func_details(f"sub_00af20c0 ({rva_to_method_name.get(0x00af20c0)})", 0x00af20c0)

# Also find ScoutPriorities and SpecificallyScouted types across all images
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules:
        continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if any(k in tname for k in ("ScoutPriorit", "SpecificallyScouted", "HumanPersonSearch", "ScoutingCentre")):
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"\n=== [{iname}] Type {ti}: {tname} ===")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
