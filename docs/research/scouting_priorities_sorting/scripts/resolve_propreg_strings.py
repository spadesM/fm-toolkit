import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, rva_to_method_name, dump_func_details, va_to_off, image_base
)

for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if "ScoutPlayerPrioritiesReference" in name or "SpecificallyScoutedPersonReference" in name:
            print(f"0x{rva:08x}: {name}")

print("\nDumping GetValueInternal for both:")
for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if name in ("ScoutPlayerPrioritiesReference.GetValueInternal", "SpecificallyScoutedPersonReference.GetValueInternal"):
            dump_func_details(name, rva, 0x350)
