import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING ===")
for name, rva in [
    ("Bindings.Create", 0x014bf980),
    ("Bindings.Bind", 0x014bee30),
    ("Bindings.Unbind", 0x014c63d0),
    ("Bindings.Set", 0x014c5740),
    ("SortData.HasReceived", 0x015a4040),
]:
    end = rva_to_end.get(rva, rva + 0x300)
    dump_func_details(name, rva, end - rva)
