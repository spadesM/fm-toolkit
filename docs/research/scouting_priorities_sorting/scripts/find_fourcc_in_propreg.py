import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, sections, va_to_off, image_base, dump_func_details

# Dump BindingKind constructors around 0x014d6ad0 and 0x014d6b00
dump_func_details("BindingKind_ctors", 0x014d6a80, 0x100)

# Search for FourCCs of ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference in code!
fourccs = [
    0x41347977, # ScoutPlayerPrioritiesReference ID
    0x72692047, # ScoutPlayerPriorities prop 1
    0x67393649, # ScoutPlayerPriorities prop 2
    0x736a3232, # ScoutPlayerPriorities prop 3
    0x73735043, # ScoutPlayerPriorities prop 4
    0x7443314a, # SpecificallyScoutedPersonReference ID
    0x706c7972, # SpecificallyScoutedPerson prop 1
    0x644d7861, # SpecificallyScoutedPerson prop 2
    0x63594545, # SpecificallyScoutedPerson prop 3
    0x75446333, # SpecificallyScoutedPerson prop 4
    0x71754c76, # SpecificallyScoutedPerson prop 5
    0x73714e20, # SpecificallyScoutedPerson prop 6
    0x6e475773, # SpecificallyScoutedPerson prop 7
]

# In PropertyRegistration.Initialise (0x003e4f30..0x004c0000), each property registration has:
# b9 <fourcc> e8 <FourCC.op_Implicit>
off_start = va_to_off(image_base + 0x003e4f30)
off_end = va_to_off(image_base + 0x004c0000)
code = pe[off_start:off_end]

for fc in fourccs:
    pat = b"\xb9" + struct.pack("<I", fc)
    pos = 0
    hits = []
    while True:
        idx = code.find(pat, pos)
        if idx == -1:
            break
        rva = 0x003e4f30 + idx
        hits.append(hex(rva))
        pos = idx + 1
    fc_str = struct.pack("<I", fc).decode("ascii", errors="replace")
    print(f"FourCC 0x{fc:08x} ({fc_str!r}): hits in PropertyRegistration = {hits}")
