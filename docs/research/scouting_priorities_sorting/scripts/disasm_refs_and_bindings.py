import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

for name, rva in [
    ("ScoutAssignmentsReference.GetPropertiesInternal", 0x0067c1c0),
    ("ScoutAssignmentsReference.GetPropertyTypeInternal", 0x0067c450),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("SpecificallyScoutedPersonReference.DerivesFromInternal", 0x00696f50),
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0),
    ("Bindings_0x014c07e0 (Bindings.cs:3197)", 0x014c07e0),
    ("Bindings_0x014c5350 (Bindings.cs:2989)", 0x014c5350),
    ("Bindings_0x014c1180 (Bindings.cs:2935)", 0x014c1180),
]:
    end_rva = cds.rva_to_end.get(rva, rva + 512)
    dhf.dump_fast(name, rva, end_rva)
