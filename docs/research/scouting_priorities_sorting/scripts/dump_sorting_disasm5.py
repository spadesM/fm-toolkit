import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm5.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast

print("=== 1. Disassemble Bindings internal methods and SpecificallyScoutedPersonReference getters ===")
targets = [
    ("Bindings_014d0b50 (Bindings.cs:600)", 0x014d0b50),
    ("Bindings_014c3770 (Bindings.cs:2630)", 0x014c3770),
    ("Bindings_014c5820", 0x014c5820),
    ("Bindings_014c21d0", 0x014c21d0),
    ("Bindings_014ca510", 0x014ca510),
    ("HashFunc_0062e910", 0x0062e910),
    ("SpecificallyScoutedPerson_165bf680", 0x165bf680),
    ("SpecificallyScoutedPerson_165bf6a0", 0x165bf6a0),
    ("SpecificallyScoutedPerson_165bf6c0", 0x165bf6c0),
    ("SpecificallyScoutedPerson_165bf6e0", 0x165bf6e0),
    ("SpecificallyScoutedPerson_165bf740", 0x165bf740),
    ("SpecificallyScoutedPerson_165bf7a0", 0x165bf7a0),
    ("SpecificallyScoutedPerson_165bf840", 0x165bf840),
]

for name, rva in targets:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dump_fast(name, rva, end_rva)

print("\n=== 2. Find ScoutPriorities / SpecificallyScouted / PersonSearch across ALL images ===")
hdr = struct.unpack_from("<64I", meta, 0)
real_fields_off = hdr[24]

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules.get(iname, (0, 0, 0))
    ptrs_off = va_to_off(m_ptrs_va) if m_ptrs_va else 0
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if any(k in tname for k in ("ScoutPriorit", "SpecificallyScouted", "PersonSearch", "ScoutTeamPriorit")):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            print(f"\n--- [{iname}] Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, real_fields_off + fi * 12)
                print(f"  Field {fi - f_start:2d}: {get_mstr(fu[0])}")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - image_base if va else 0
                print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")

out_file.close()
print("Done!", file=sys.__stdout__)
