import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# 1. Find ScoutPriorities / SpecificallyScoutedPerson reference types and dump their methods
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
        if any(k in tname for k in ("ScoutPlayerPriorities", "SpecificallyScoutedPerson", "ScoutPriorities")):
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"=== {iname} Type {ti}: {tname} ===")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

# 2. Disassemble StreamedTable.OnSortColumn (0x015ee250) & StreamedTable_CreateColumnsFromTableViewCollection (0x015e82c0)
dump_func_details("StreamedTable.OnSortColumn", 0x015ee250)
dump_func_details("StreamedTable_CreateColumnsFromTableViewCollection", 0x015e82c0)
dump_func_details("StreamedTable.SetNoSorting", 0x015ef750)
dump_func_details("StreamedListView.SetNoSorting", 0x015a99d0)
dump_func_details("StreamedTable.TryFindSortedColumn", 0x015eff70)
