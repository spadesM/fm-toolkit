import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

for rva in [0x014c1a60, 0x014c1450]:
    end_rva = cds.rva_to_end.get(rva, rva + 0x200)
    names = cds.rva_to_method_name.get(rva, [f"func_0x{rva:08x}"])
    dhf.dump_fast(f"{', '.join(names[:2])} (0x{rva:08x})", rva, end_rva)
