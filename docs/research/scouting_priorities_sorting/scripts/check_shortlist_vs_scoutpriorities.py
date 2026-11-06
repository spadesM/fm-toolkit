import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated

print("=== 1. Dump ScoutPlayerPrioritiesReference.GetPropertyTypeInternal (0x0067d500) ===")
dump_func_details("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500, rva_to_end.get(0x0067d500, 0x0067d610) - 0x0067d500)

print("\n=== 2. Check FourCCs in ScoutPlayerPrioritiesReference.GetPropertiesInternal (0x0067d360) ===")
# From lines 375, 380, 384, 389 of steps/3156/output.txt:
# b9 47 20 69 72 -> 0x72692047 ('G ir')
# b9 49 36 39 67 -> 0x67393649 ('I69g')
# b9 32 32 6a 73 -> 0x736a3232 ('22js')
# b9 43 50 73 73 -> 0x73735043 ('CPss')
for fcc in [0x72692047, 0x67393649, 0x736a3232, 0x73735043, 0x724c4e4d, 0x724c4e4e, 0x724c4e4f]:
    pat = b'\xb9' + struct.pack('<I', fcc)
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        print(f"  FourCC 0x{fcc:08x} ({struct.pack('<I', fcc)!r}) at RVA 0x{rva:08x}")
        # Dump 40 bytes before and after in PropertyRegistration.Initialise if RVA < 0x004c0000
        if rva < 0x004c0000:
            dump_annotated(f"PropReg around 0x{rva:08x}", rva - 0x20, 0x60)
        pos = idx + 1
