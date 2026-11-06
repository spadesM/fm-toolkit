import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, dump_func_details, rva_to_method_name, va_to_off, off_to_va, image_base,
    types_off, types_sz, methods_off, get_mstr, hdr
)

for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if "ScoutPlayerPriorities" in n:
            print(f"0x{rva:08x}: {n}")

dump_func_details("ScoutPlayerPrioritiesReference.AcceptsPropertyInternal", 0x0067d0b0, 0x5b0)
