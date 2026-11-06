import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
from check_deep_sorting import (
    pe, meta, image_base, va_to_off, rva_to_end, rva_to_method_name,
    get_mstr, methods_off, types_off, images_off, images_sz, modules, dump_func_details
)
from annotate_sorting_usym import dump_annotated, usym_map

hdr = struct.unpack_from("<64I", meta, 0)
# Print all 64 header ints to see metadata table offsets
for i in range(0, 64, 2):
    print(f"hdr[{i:2d}..{i+1:2d}]: off=0x{hdr[i]:08x} sz=0x{hdr[i+1]:08x} (cnt={hdr[i+1]//4 if hdr[i+1] else 0})")

# List all methods of StreamedListView (TypeDef 5791) and StreamedTable (TypeDef 5967)
_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)
for ti in (5786, 5787, 5788, 5789, 5790, 5791, 5967):
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
        if any(w in mname.lower() for w in ("sort", "init", "header", "bind", "compare", "242", "243", "244", "245", "246", "247")) or ti != 5967:
            print(f"  [{mi}] {mname}: RVA=0x{rva:08x} size={sz}")
