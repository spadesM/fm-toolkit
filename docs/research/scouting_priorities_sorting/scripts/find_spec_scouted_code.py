import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

# 1. Disassemble 0x002ae590 and 0x00696f50..0x00696f80
for name, rva in [
    ("AutogenBindings_0x002ae590", 0x002ae590),
    ("SpecificallyScoutedPersonReference.GetInstance (0x00696f70)", 0x00696f70),
    ("SpecificallyScoutedPersonReference.get_Identifier (0x00697370)", 0x00697370),
]:
    end_rva = cds.rva_to_end.get(rva, rva + 128)
    dhf.dump_fast(name, rva, end_rva)

# 2. Search PE for 4a 31 43 74 (0x7443314a) and the 7 FourCCs
pe = cds.pe
for label, val in [
    ("SpecificallyScoutedPerson (0x7443314a)", 0x7443314a),
    ("Prop1 (0x706c7972)", 0x706c7972),
    ("Prop2 (0x644d7861)", 0x644d7861),
    ("Prop3 (0x63594545)", 0x63594545),
    ("Prop4 (0x75446333)", 0x75446333),
    ("Prop5 (0x71754c76)", 0x71754c76),
    ("Prop6 (0x73714e20)", 0x73714e20),
    ("Prop7 (0x6e475773)", 0x6e475773),
]:
    pat = struct.pack("<I", val)
    print(f"\n=== Occurrences of {label} ===")
    pos = 0
    hits = []
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = cds.off_to_va(idx)
        rva = va - cds.image_base if va else 0
        hits.append((idx, rva))
        pos = idx + 1
    for idx, rva in hits[:30]:
        # find containing function in pdata
        func_rva = None
        for b_rva, e_rva in cds.rva_to_end.items():
            if b_rva <= rva < e_rva:
                func_rva = b_rva
                break
        mnames = cds.rva_to_method_name.get(func_rva, []) if func_rva else []
        print(f"  off=0x{idx:x} RVA=0x{rva:08x} in func 0x{func_rva or 0:08x} ({', '.join(mnames[:3])})")
