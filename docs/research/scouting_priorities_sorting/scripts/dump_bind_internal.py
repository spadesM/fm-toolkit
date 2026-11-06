import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING ===")
for name, rva in [
    ("Bindings.Bind_internal", 0x014beef0),
    ("Bindings.SetInternal", 0x014c3770),
    ("Bindings.UpdateNodeDataTarget", 0x014c6590),
]:
    end = rva_to_end.get(rva, rva + 0x400)
    dump_func_details(name, rva, end - rva)
