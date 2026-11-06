import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

for b_rva, names in sorted(cds.rva_to_method_name.items()):
    if 0x015df000 <= b_rva <= 0x015e0500:
        e_rva = cds.rva_to_end.get(b_rva, b_rva + 0x100)
        print(f"0x{b_rva:08x}..0x{e_rva:08x}: {names}")
        dhf.dump_fast(f"{names[0]}", b_rva, e_rva)
