import sys
sys.path.insert(0, r"c:\Repos\fm26save")
from check_deep_sorting import dump_func_details, pe, meta, rva_to_end, methods_off, types_off, images_off, get_mstr, va_to_off, off_to_va, image_base
from fm26save.binary_decompiler import resolve_fm_install_dir, fourcc_to_ascii
import struct

# Find FM.UI.dll module
fm_ui_str_off = pe.find(b"\x00FM.UI.dll\x00") + 1
fm_ui_mod_off = pe.find(struct.pack("<Q", off_to_va(fm_ui_str_off)))
name_va, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, fm_ui_mod_off)
ptrs_off = va_to_off(m_ptrs_va)

for ti in [860, 909, 910]:
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n=== Type {ti}: {tname} ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
        rva = va - image_base if va else 0
        sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
        print(f"  {mname}: RVA=0x{rva:08x} (size={sz})")
        if mname in ("GetPropertyTypeInternal", "GetPropertiesInternal", "GetContextsInternal", "AcceptsPropertyInternal", "GetPropertyDescriptionInternal", "GetInstance"):
            dump_func_details(f"{tname}.{mname}", rva, sz)
