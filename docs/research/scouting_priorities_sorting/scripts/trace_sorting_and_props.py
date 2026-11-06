import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll"
pe = pefile.PE(pe_path, fast_load=True)
data = open(pe_path, "rb").read()

import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_fast import dump_fast, rva_to_off, rvas_to_names, str_by_off

# 1. Check forward property registrations for J1Ct and ao3d
prop_init_off = rva_to_off(0x00656ac0)
prop_init_end = rva_to_off(0x00656ac0 + 250000)

for tag in [b"J1Ct", b"ao3d", b"m7Qr", b"xK9p"]:
    idx = prop_init_off
    print(f"=== Forward Property Registrations for {tag.decode()} ===")
    while True:
        idx = data.find(b"\xb9" + tag, idx, prop_init_end)
        if idx == -1:
            break
        rva = pe.get_rva_from_offset(idx)
        # Disassemble from idx - 32 to idx + 96 to see exact instructions and string literals
        dump_fast(f"{tag.decode()} @ 0x{rva:08x}", rva - 0x20, rva + 0x60)
        idx += 5

# 2. Disassemble SpecificallyScoutedPersonReference methods (from steps/4188/output.txt)
print("=== SpecificallyScoutedPersonReference methods ===")
dump_fast("SpecificallyScoutedPersonReference.GetPropertyInternal", 0x00696f70, 0x00697250)

# 3. Disassemble Bindings.CreateAlias (0x014bf980) and 0x014c1450 and SetupRow (0x015aa320 .. 0x015aa620)
print("=== SetupRow full (0x015aa320 .. 0x015aa600) ===")
dump_fast("<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x015aa600)

print("=== Bindings.CreateAlias (0x014bf980) ===")
dump_fast("Bindings.CreateAlias", 0x014bf980, 0x014bfd00)
