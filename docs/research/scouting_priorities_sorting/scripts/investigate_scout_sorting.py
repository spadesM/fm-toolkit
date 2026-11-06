import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from parse_st_data_exact import get_ref_bytes

# 1. Find ScoutPlayerPrioritiesReference, SpecificallyScoutedPersonReference, SpecificallyScoutedTeamReference
target_types = (
    "ScoutPlayerPrioritiesReference",
    "SpecificallyScoutedPersonReference",
    "SpecificallyScoutedTeamReference",
    "ScoutTeamPrioritiesReference",
)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules:
        continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    if ptrs_off < 0 or m_cnt_mod == 0:
        continue
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname in target_types or "SpecificallyScouted" in tname or "ScoutPlayerPriorities" in tname:
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            f_start = tu[8]
            f_cnt = tu[15] & 0xFFFF
            print(f"\n=== {iname} :: {tname} (Type {ti}) ===")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                print(f"  Field {fi - f_start}: {get_mstr(fu[0])}")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
                if rva:
                    dump_func_details(f"{tname}.{mname}", rva, sz)
