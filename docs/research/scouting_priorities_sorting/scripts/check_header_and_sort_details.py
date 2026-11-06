import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, get_mstr, image_base, va_to_off, rva_to_end,
    images_off, images_sz, types_off, methods_off, modules,
    rva_to_method_name, dump_func_details
)

# 1. Find all nested types of StreamedListView and StreamedTable in FM.UI.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "FM.UI.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("SortData", "SortComparer", "Header", "ColumnConfig", "ColumnMetadata"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"=== Type {ti}: {tname} (declaringType={tu[3]}) ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                    rva = va - image_base if va else 0
                    sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                    print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

dump_func_details("Header..ctor", 0x015dfab0)
dump_func_details("Header.Bind", 0x015df4f0)
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040)
dump_func_details("StreamedTable.SetSorting(1)", 0x015efc40)
dump_func_details("StreamedTable.SortDataFromView", 0x015efeb0)
dump_func_details("StreamedTable.RebuildInternal", 0x015ee9c0)
dump_func_details("StreamedListView.Rebuild", 0x015a8eb0)
