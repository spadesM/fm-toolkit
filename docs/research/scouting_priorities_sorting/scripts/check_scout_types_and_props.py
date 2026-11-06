import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# 1. Dump SpecificallyScoutedPersonReference methods
dump_func_details("SpecificallyScoutedPersonReference.get_ID", 0x00697370)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200)
dump_func_details("ScoutPlayerPrioritiesReference.get_ID", 0x0067d650)

# 2. Search for 0x6646634b (4b 63 46 66) in code sections to see which Reference class has that ID!
pat = struct.pack("<I", 0x6646634b)
for sname, rva_s, vsz, raw_ptr, rawsz in sections:
    if sname not in (".text", "il2cpp"):
        continue
    pos = raw_ptr
    end = raw_ptr + rawsz
    while True:
        idx = pe.find(pat, pos, end)
        if idx == -1:
            break
        hit_rva = rva_s + (idx - raw_ptr)
        best_rva = max((r for r in rva_to_method_name if r <= hit_rva), default=0)
        print(f"Hit 0x6646634b at RVA 0x{hit_rva:08x} in {rva_to_method_name.get(best_rva)} (0x{best_rva:08x})")
        pos = idx + 1
