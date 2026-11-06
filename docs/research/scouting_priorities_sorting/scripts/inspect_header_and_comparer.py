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
for ti in range(5950, 5968):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n=== Type {ti}: {tname} (methods={m_cnt}) ===")
    if ti != 5967:
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
            rva = va - image_base if va else 0
            sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
            print(f"  [{mi}] {mname}: RVA=0x{rva:08x} size={sz}")

dump_func_details("SortComparer.Compare(int, int)", 0x015a3c60)
dump_annotated("SortComparer.Compare(int, int)", 0x015a3c60)
dump_func_details("SortComparer.Compare(object, object)", 0x015a3d30)
dump_annotated("SortComparer.Compare(object, object)", 0x015a3d30)
dump_annotated("StreamedTable.MakeColumnHeader", 0x015eac30)
dump_func_details("Header..ctor", 0x015dfab0)
dump_annotated("Header..ctor", 0x015dfab0)
dump_func_details("StreamedTable.InitialiseColumns", 0x015ea870)
dump_annotated("StreamedTable.InitialiseColumns", 0x015ea870)
dump_func_details("StreamedTable.BindHeader", 0x015e6230)
dump_annotated("StreamedTable.BindHeader", 0x015e6230)
dump_func_details("StreamedTable.BindToDataInternal", 0x015e6d70)
dump_annotated("StreamedTable.BindToDataInternal", 0x015e6d70)
