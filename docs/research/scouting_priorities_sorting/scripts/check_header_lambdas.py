import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, get_mstr, image_base, va_to_off, rva_to_end,
    images_off, images_sz, types_off, types_sz, methods_off, fields_off, modules,
    rva_to_method_name, dump_func_details
)

# 1. Check methods around Header (0x015df200 .. 0x015e1a20)
print("=== All methods in 0x015df200 .. 0x015e1a20 ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015df200 <= rva <= 0x015e1a20:
        print(f"  0x{rva:08x}: {', '.join(rva_to_method_name[rva])}")
        dump_func_details(rva_to_method_name[rva][0], rva)

# 2. Check methods around MakeColumnHeader lambdas (0x015f0500 .. 0x015f2a00)
print("\n=== All methods in 0x015f0500 .. 0x015f2a00 ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015f0500 <= rva <= 0x015f2a00:
        names = rva_to_method_name[rva]
        if any("b__" in n or "g__" in n or "Header" in n or "Sort" in n for n in names):
            print(f"  0x{rva:08x}: {', '.join(names)}")
            dump_func_details(names[0], rva)
