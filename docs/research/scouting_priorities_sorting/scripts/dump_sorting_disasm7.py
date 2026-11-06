import struct, sys, glob, os
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm7.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast

hdr = struct.unpack_from("<64I", meta, 0)
real_fields_off = hdr[24]

print("=== 1. Inspect ScoutPlayerPrioritiesReference (Type 860) and PersonSearchReference (Type 724) ===")
_, m_cnt_mod, m_ptrs_va = modules["FM.UI.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "FM.UI.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in [860, 861, 724]:
            tu = struct.unpack_from("<22i", meta, types_off + (t_start + ti) * 88)
            tname = get_mstr(tu[0])
            if "ScoutPlayerPriorit" not in tname and "ScoutTeamPriorit" not in tname and "PersonSearch" not in tname:
                # ti is already global type index
                tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
                tname = get_mstr(tu[0])
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            print(f"\n--- Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - image_base if va else 0
                print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")
                if rva > 0 and ti in (860, 861):
                    end_rva = rva_to_end.get(rva, rva + 0x150)
                    dump_fast(f"{tname}.{mname}", rva, end_rva)

print("\n=== 2. Check all StreamedListView and StreamedTable methods for Reorderable / m_reorderable (+0x4e4) / m_disableSorting (+0x7a0) ===")
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in [5791, 5967]: # StreamedListView, StreamedTable
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            print(f"\n--- Type {ti}: {tname} (methods={m_cnt}) ---")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - image_base if va else 0
                print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")

out_file.close()
print("Done!", file=sys.__stdout__)
