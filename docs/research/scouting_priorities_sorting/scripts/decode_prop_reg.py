import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# Let's search ALL type names and method names in global-metadata.dat for Scout / Priorit / Specifically
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    mod_info = modules.get(iname)
    m_cnt_mod, ptrs_off = (mod_info[1], va_to_off(mod_info[2])) if mod_info else (0, -1)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        ns = get_mstr(tu[1])
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        matched_type = any(k in tname for k in ("SpecificallyScouted", "ScoutPlayerPriorit", "ScoutPriorit"))
        if matched_type:
            print(f"=== [{iname}] {ns}.{tname} ===")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            if matched_type or any(k in mname for k in ("SpecificallyScouted", "ScoutPlayerPriorit", "ScoutPriorit")):
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (0 <= rid < m_cnt_mod and ptrs_off > 0) else 0
                rva = va - image_base if va else 0
                print(f"  [{iname}] {tname}.{mname}: RVA=0x{rva:08x}")

# Also let's search PE for FourCCs of SpecificallyScoutedPersonReference properties:
# 0x706c7972 (plyr), 0x644d7861 (dMxa), 0x63594545 (cYEE), 0x75446333 (uDc3), 0x71754c76 (quLv), 0x73714e20 (sqN ), 0x6e475773 (nGWs)
# and Type ID of SpecificallyScoutedPersonReference (let's check get_ID at 0x00697370) and ScoutPlayerPrioritiesReference (get_ID at 0x0067d650)
dump_func_details("ScoutPlayerPrioritiesReference.get_ID", 0x0067d650, 64)
dump_func_details("SpecificallyScoutedPersonReference.get_ID", 0x00697370, 64)
