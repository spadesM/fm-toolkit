import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr
from annotate_sorting_usym import dump_annotated

# 1. Inspect PropertyRegistration.Initialise around 0x003fdcb7
def rva_to_off(rva): return va_to_off(image_base + rva)
def off_to_rva(off): return off_to_va(off) - image_base

print("=== PropertyRegistration.Initialise around 0x003fdcb7 ===")
off = rva_to_off(0x003fdc00)
chunk = pe[off:off+0x200]
for i in range(0, len(chunk), 16):
    rva = 0x003fdc00 + i
    bs = " ".join(f"{b:02x}" for b in chunk[i:i+16])
    print(f"  0x{rva:08x}: {bs}")
    # check for CALLs (e8) or LEA RIP (48 8d 05 / 4c 8d 05)
    for j in range(16):
        if i + j + 5 <= len(chunk) and chunk[i+j] == 0xe8:
            rel = struct.unpack_from("<i", chunk, i+j+1)[0]
            t = rva + j + 5 + rel
            print(f"    +0x{i+j:03x} (0x{rva+j:08x}): CALL 0x{t:08x} -> {rva_to_method_name.get(t)}")
        if i + j + 7 <= len(chunk) and chunk[i+j] in (0x48, 0x4c) and chunk[i+j+1] == 0x8d and (chunk[i+j+2] & 0xc7) == 0x05:
            rel = struct.unpack_from("<i", chunk, i+j+3)[0]
            t = rva + j + 7 + rel
            print(f"    +0x{i+j:03x} (0x{rva+j:08x}): LEA RIP 0x{t:08x} -> {rva_to_method_name.get(t)}")

# 2. Also search for SpecificallyScoutedPersonReference's properties in PropertyRegistration.Initialise
# What are the property IDs in SpecificallyScoutedPersonReference.GetPropertiesInternal (0x00696f80)?
dump_func_details("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80)
dump_func_details("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0)
dump_func_details("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360)
dump_func_details("StreamedTable_CreateColumnsFromTableViewCollection.ExecuteInternal", 0x0152af20)
dump_func_details("StreamedTable.CreateColumnsFromTableViewCollection", 0x015e82c0)
