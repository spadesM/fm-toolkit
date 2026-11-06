import struct
from check_deep_sorting import (
    pe, image_base, va_to_off, dump_func_details, rva_to_method_name,
    meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end
)

# List all methods of Header, StreamedTable, StreamedListView, SortData, and their nested types
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
            if tname in ("Header", "SortData", "RowData", "CellData", "PathData", "Column") or "DisplayClass" in tname:
                # Check parent or method names
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                mnames = [get_mstr(struct.unpack_from("<7i4H", meta, methods_off + mi * 36)[0]) for mi in range(m_start, m_start + m_cnt)]
                if tname in ("Header", "SortData", "RowData", "CellData", "PathData", "Column") or any("MakeColumnHeader" in m or "Header" in m or "Sort" in m for m in mnames):
                    print(f"=== Type {ti}: {tname} ===")
                    for mi in range(m_start, m_start + m_cnt):
                        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                        mname = get_mstr(mu[0])
                        rid = (mu[6] & 0xFFFFFF) - 1
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                        rva = va - image_base if va else 0
                        sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                        print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

dump_func_details("Bindings.Create", 0x014bf980)
dump_func_details("Bindings.Bind", 0x014beef0)
dump_func_details("Bindings.Set(Key)", 0x014c5740)
dump_func_details("0x00e030e0 (called in MakeColumnHeader +0x357)", 0x00e030e0)
dump_func_details("0x009b93e0 (called in MakeColumnHeader +0x10f)", 0x009b93e0)
dump_func_details("0x00b16e00 (called in Header..ctor +0x11e)", 0x00b16e00)
