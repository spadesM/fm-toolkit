import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, pe, va_to_off, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end

for name, rva in [
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("ScoutingCentreEntryItemReference.AcceptsPropertyInternal", 0x00680c10),
    ("ScoutingCentreEntryItemReference.GetPropertiesInternal", 0x00680ca0),
    ("ScoutingCentreEntryItemReference.GetPropertyTypeInternal", 0x00680f20),
    ("StreamedListView.SetDirty", 0x015a9780),
    ("SortData.HasReceived", 0x015a4040),
]:
    dump_func_details(name, rva)

# Also list all methods of StreamedListView and VirtualisedList in SI.Bindable.dll
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
            if tname in ("StreamedListView", "StreamedTable"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"\n=== [{iname}] {tname} methods ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    if any(k in mname.lower() for k in ("sort", "dirty", "update", "header", "init", "view", "column", "reorder", "drag")):
                        rid = (mu[6] & 0xFFFFFF) - 1
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                        rva = va - image_base if va else 0
                        sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                        print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
