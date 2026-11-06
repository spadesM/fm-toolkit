import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va, get_mstr,
    types_off, types_sz, fields_off, fields_sz, methods_off, methods_sz
)

byval_to_ti = {}
num_types = types_sz // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    byval_to_ti[tu[5]] = ti

target_tis = {13468, 5791, 5967}
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    decl_ti = byval_to_ti.get(tu[2], -1)
    if ti in target_tis or decl_ti in target_tis:
        tname = get_mstr(tu[0])
        tns = get_mstr(tu[1])
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        parent_ti = byval_to_ti.get(tu[3], -1)
        print(f"\n=== Type[{ti}] {tns}.{tname} (decl_ti={decl_ti}, parent_ti={parent_ti}, fields={f_cnt}, methods={m_cnt}) ===")
        for fi in range(f_start, f_start + f_cnt):
            fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
            fname = get_mstr(fu[0])
            print(f"  Field[{fi - f_start:2d}] (global {fi}): {fname} (type_byval={fu[1]})")
