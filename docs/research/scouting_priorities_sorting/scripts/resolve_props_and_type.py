import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import resolve_data_rva
from check_deep_sorting import pe, image_base, off_to_va

prop_ids = [
    (0x706c7972, "SpecificallyScoutedPerson prop 1"),
    (0x644d7861, "SpecificallyScoutedPerson prop 2"),
    (0x63594545, "SpecificallyScoutedPerson prop 3"),
    (0x75446333, "SpecificallyScoutedPerson prop 4"),
    (0x71754c76, "SpecificallyScoutedPerson prop 5"),
    (0x73714e20, "SpecificallyScoutedPerson prop 6"),
    (0x6e475773, "SpecificallyScoutedPerson prop 7"),
    (0x72692047, "ScoutPlayerPriorities prop 1"),
    (0x67393649, "ScoutPlayerPriorities prop 2"),
    (0x736a3232, "ScoutPlayerPriorities prop 3"),
    (0x73735043, "ScoutPlayerPriorities prop 4"),
]

print("=== 1. Exact Property Names in PropertyRegistration.Initialise ===")
for val, label in prop_ids:
    pat = b"\xb9" + struct.pack("<I", val)
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003e4f30 <= rva <= 0x004c5d06:
            chunk = pe[idx : idx + 120]
            names_found = []
            for i in range(len(chunk) - 7):
                if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
                    disp = struct.unpack_from("<i", chunk, i + 3)[0]
                    insn_rva = rva + i
                    trva = insn_rva + 7 + disp
                    names_found.append(resolve_data_rva(trva))
            print(f"  {label} (0x{val:08x}) at RVA 0x{rva:08x} -> {names_found}")
        pos = idx + 1

print("\n=== 2. ProcessSortingDataChanged [rip + 0x0185e09d] at RVA 0x015a8e06 ===")
print("  0x02e06ea8 ->", resolve_data_rva(0x02e06ea8))
