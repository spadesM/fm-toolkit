import struct, bisect
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, image_base, off_to_va, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, get_mstr, modules, va_to_off

sorted_mrvas = sorted(rva_to_method_name.keys())

fourccs = [
    ("SpecificallyScoutedPlayers ('22js')", 0x736a3232),
    ("ScoutPlayerPrioritiesReference ('wy4A')", 0x41347977),
    ("SpecificallyScoutedPersonReference ('J1Ct')", 0x7443314a),
    ("SpecificallyScoutedPerson.Priority ('axMd')", 0x644d7861),
    ("SpecificallyScoutedPerson.ScoutDuration ('3cDu')", 0x75446333),
]

for name, val in fourccs:
    pat = struct.pack("<I", val)
    print(f"\n=== Occurrences of {name} (0x{val:08x}) ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        bi = bisect.bisect_right(sorted_mrvas, rva) - 1
        mname = "unknown"
        if bi >= 0:
            mrva = sorted_mrvas[bi]
            end_rva = rva_to_end.get(mrva, mrva + 0x1000)
            if rva <= end_rva + 0x100:
                mname = f"{rva_to_method_name[mrva][:3]} (0x{mrva:08x} + 0x{rva-mrva:x})"
        print(f"  RVA 0x{rva:08x} in {mname}")
        pos = idx + 1

print("\n=== Relevant Types in Metadata ===")
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    nspace = get_mstr(tu[1])
    if tname in ("DataReference", "InteropReference", "StaticDataReference", "PolymorphicDataReference") or "SpecificallyScouted" in tname or "ScoutPlayerPriorities" in tname:
        print(f"Type {ti}: {nspace}.{tname} (tu[4]={tu[4]}, methods={tu[16]&0xFFFF})")
