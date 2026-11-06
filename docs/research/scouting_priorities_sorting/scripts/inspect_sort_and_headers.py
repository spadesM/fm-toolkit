import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from check_deep_sorting import (
    pe, meta, image_base, va_to_off, rva_to_end, rva_to_method_name,
    get_mstr, methods_off, types_off, images_off, images_sz, modules, dump_func_details
)
from annotate_sorting_usym import dump_annotated

_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)
for ti in range(5775, 5786):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n=== Type {ti}: {tname} (methods={m_cnt}) ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
        rva = va - image_base if va else 0
        sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
        print(f"  [{mi}] {mname}: RVA=0x{rva:08x} size={sz}")

dump_func_details("StreamedListView.PostSortingDataChanged", 0x015a8610)
dump_annotated("StreamedListView.PostSortingDataChanged", 0x015a8610)
dump_func_details("StreamedListView.SetSortingBinding(index, path, asc)", 0x015a9ae0)
dump_annotated("StreamedListView.SetSortingBinding(index, path, asc)", 0x015a9ae0)
dump_func_details("StreamedListView.StateChanged", 0x015a9c80)
dump_annotated("StreamedListView.StateChanged", 0x015a9c80)
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040)
dump_annotated("StreamedTable.TrySetColumnsAndSort", 0x015f0040)
dump_func_details("StreamedTable.ApplyPersistedSortingState", 0x015e58c0)
dump_annotated("StreamedTable.ApplyPersistedSortingState", 0x015e58c0)
dump_func_details("StreamedTable.UpdateSortColum", 0x015f1380)
dump_annotated("StreamedTable.UpdateSortColum", 0x015f1380)
dump_func_details("StreamedTable.MakeColumnHeader", 0x015eac30)
dump_annotated("StreamedTable.MakeColumnHeader", 0x015eac30)
dump_func_details("StreamedTable.InitialiseColumns", 0x015ea870)
dump_annotated("StreamedTable.InitialiseColumns", 0x015ea870)
