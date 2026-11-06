import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# 1. Let's find all types with ScoutPriorit or SpecificallyScouted or ScoutedPerson in global-metadata.dat
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
        ns = get_mstr(tu[1])
        if any(k in tname for k in ("ScoutPriorit", "SpecificallyScouted", "ScoutedPerson", "StreamedTable", "StreamedListView")):
            print(f"Type {ti}: {ns}.{tname} (in {iname})")
            if "Scout" in tname:
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off >= 0 and 0 <= rid < m_cnt_mod) else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

print("\n--- Dumping SpecificallyScoutedPersonReference & StreamedTable/ListView methods ---")
for name, rva in [
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.BindToDataInternal", 0x015e6d70),
    ("StreamedListView.SetSortingBinding", 0x015a9ae0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.ResetIndices", 0x015a9420),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
