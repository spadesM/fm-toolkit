import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_class_methods import meta, hdr, get_mstr, va_to_off, image_base, pe, modules, methods_off, types_off, images_off, images_sz
from dump_headers_fast import dump_fast

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules: continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if any(k in tname for k in ["SpecificallyScouted", "ScoutPlayerPriorities", "ScoutPriorit"]):
            print(f"\n=== {iname} :: {tname} (ti={ti}) ===")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                rva = 0
                if 0 <= rid < m_cnt_mod:
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                    if va > 0: rva = va - image_base
                print(f"  [mi={mi}] 0x{rva:08x} {mname} (slot={mu[10]})")

print("\n" + "="*80)
dump_fast("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360, 0x0067d500)
dump_fast("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80, 0x00697200)
dump_fast("StreamedTable.FindDataToBind (0x015f1380)", 0x015f1380, 0x015f1600)
dump_fast("StreamedTable.GetData (0x015e9450)", 0x015e9450, 0x015e9600)
