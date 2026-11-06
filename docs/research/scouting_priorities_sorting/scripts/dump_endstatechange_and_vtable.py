import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# Dump StreamedListView.BeginStateChange (0x015a47a0), EndStateChange (0x015a5350), and 0x00abdcc0, 0x00af20c0, 0x00af8a80
for name, rva in [
    ("StreamedListView.BeginStateChange", 0x015a47a0),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("Func_0x00abdcc0", 0x00abdcc0),
    ("Func_0x00af20c0", 0x00af20c0),
    ("Func_0x00af8a80", 0x00af8a80),
    ("StreamedTable.UpdatePersistedColumnSortingData", 0x015f1290),
]:
    dump_func_details(name, rva)

# Also list ALL methods of StreamedListView (Type 5791) and StreamedTable (Type 5967) with their RVAs so we can see what vtable methods exist!
_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)
for ti in (5791, 5967):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start, m_cnt = tu[9], tu[16] & 0xFFFF
    print(f"\n=== All methods of {tname} (Type {ti}) ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
        rva = va - image_base if va else 0
        flags = mu[7]
        vslot = mu[8]
        print(f"  [{mi-m_start:3d}] {mname} (vslot={vslot}, flags=0x{flags:04x}): RVA=0x{rva:08x}")
