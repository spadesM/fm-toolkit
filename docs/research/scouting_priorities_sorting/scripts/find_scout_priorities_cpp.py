import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, image_base, off_to_va, va_to_off, rva_to_method_name, dump_func_details

for s in [b"ScoutPriorities", b"SpecificallyScoutedPlayers", b"SpecificallyScoutedPerson", b"SpecificallyScoutedTeams", b"J1Ct"]:
    idx = 0
    hits = []
    while True:
        idx = pe.find(s, idx)
        if idx == -1:
            break
        hits.append(idx)
        idx += 1
    print(f"String {s}: {len(hits)} hits -> {[hex(off_to_va(h) - image_base) for h in hits[:10]]}")
    for h in hits[:5]:
        # find xrefs to this string in code (LEA reg, [rip + disp])
        target_rva = off_to_va(h) - image_base
        print(f"  String at RVA 0x{target_rva:08x}: {pe[h:h+64].split(b'\\x00')[0]}")
