import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

pe = cds.pe
for label, val in [
    ("ScoutPriorities (0x76376148)", 0x76376148),
    ("SpecificallyScoutedPlayers (0x736a3232)", 0x736a3232),
    ("SpecificallyScoutedPlayersCount (0x73735043)", 0x73735043),
]:
    pat = struct.pack("<I", val)
    print(f"\n=== Occurrences of {label} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = cds.off_to_va(idx)
        rva = va - cds.image_base if va else 0
        func_rva = None
        for b_rva, e_rva in cds.rva_to_end.items():
            if b_rva <= rva < e_rva:
                func_rva = b_rva
                break
        mnames = cds.rva_to_method_name.get(func_rva, []) if func_rva else []
        print(f"  off=0x{idx:x} RVA=0x{rva:08x} in func 0x{func_rva or 0:08x} ({', '.join(mnames[:3])})")
        if func_rva and func_rva != 0x003e4f30:
            end_rva = cds.rva_to_end.get(func_rva, func_rva + 512)
            dhf.dump_fast(f"{label} hit in {mnames}", func_rva, end_rva)
        pos = idx + 1
