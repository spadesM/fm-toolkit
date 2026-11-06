import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, dump_func_details, rva_to_method_name, va_to_off, image_base,
    types_off, types_sz, methods_off, fields_off, fields_sz, get_mstr, hdr
)

props_off, props_sz = hdr[10], hdr[11]

# 1. Search all types for ScoutPriorit or SpecificallyScouted
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    ns = get_mstr(tu[1])
    if any(k in tname for k in ("ScoutPriorit", "SpecificallyScouted", "ScoutTeamPriorit", "RecruitmentScout")):
        print(f"\n=== Type #{ti}: {ns}.{tname} ===")
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            print(f"  Method: {mname}")

# 2. Search all methods in rva_to_method_name for ScoutPriorit or SpecificallyScouted
print("\n=== Methods in rva_to_method_name ===")
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(k in n for k in ("ScoutPriorit", "SpecificallyScouted", "ScoutTeamPriorit")):
            print(f"  0x{rva:08x}: {n}")

# 3. Dump rest of StreamedTable.UxmlSerializedData.Deserialize
dump_func_details("StreamedTable.UxmlSerializedData.Deserialize_part2", 0x015f3cb0, 0x500)
