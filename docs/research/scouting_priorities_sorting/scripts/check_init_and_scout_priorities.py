import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr
from annotate_sorting_usym import dump_annotated

def rva_to_off(rva): return va_to_off(image_base + rva)
def off_to_rva(off): return off_to_va(off) - image_base

# 1. Search for types/methods related to InitialiseStreamedTableFromViewCollection or ViewCollection or ScoutPriorities or SpecificallyScouted
td_off = hdr[160 // 4]
td_cnt = hdr[164 // 4] // 88
md_off = hdr[32 // 4]

for ti in range(td_cnt):
    off = td_off + ti * 88
    name_idx, ns_idx = struct.unpack_from("<II", meta, off)
    tname = get_mstr(name_idx)
    if any(k in tname for k in ["ViewCollection", "ScoutPriorit", "SpecificallyScouted", "StreamedTable"]):
        m_cnt = struct.unpack_from("<H", meta, off + 76)[0]
        print(f"Type {ti}: {tname} (methods={m_cnt})")

# Also search rva_to_method_name values
print("\nMatching rva_to_method_name:")
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(k in n for k in ["ViewCollection", "ScoutPriorit", "SpecificallyScouted"]):
            print(f"  0x{rva:08x}: {n}")

# 2. Search .text for 0x736a3232 ('22js' = SpecificallyScoutedPlayers) and 0x7443314a ('J1Ct' = SpecificallyScoutedPersonReference)
# and 0x39384942 ('BI89' = ScoutPriorities) and 0x746b3158 ('X1kt' = itemmoved)
print("\nSearching .text for hashes:")
text_start = rva_to_off(0x00001000)
text_end = rva_to_off(0x02400000)
sorted_rvas = sorted(rva_to_method_name.keys())
import bisect

for label, val in [("SpecificallyScoutedPlayers (0x736a3232)", 0x736a3232),
                   ("SpecificallyScoutedPersonReference (0x7443314a)", 0x7443314a),
                   ("ScoutPriorities (0x39384942)", 0x39384942),
                   ("itemmoved (0x746b3158)", 0x746b3158)]:
    pat = struct.pack("<I", val)
    pos = text_start
    print(f"\n  Hash {label}:")
    while True:
        idx = pe.find(pat, pos, text_end)
        if idx == -1:
            break
        rva = off_to_rva(idx)
        bi = bisect.bisect_right(sorted_rvas, rva) - 1
        fn_rva = sorted_rvas[bi] if bi >= 0 else 0
        fn_name = rva_to_method_name.get(fn_rva, ["?"])
        print(f"    at RVA 0x{rva:08x} in 0x{fn_rva:08x} ({fn_name})")
        pos = idx + 1
