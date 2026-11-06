import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr
from annotate_sorting_usym import dump_annotated, resolve_rip_va

def rva_to_off(rva): return va_to_off(image_base + rva)
def off_to_rva(off): return off_to_va(off) - image_base

print("0x02dfbe90:", resolve_rip_va(image_base + 0x02dfbe90))
print("0x02e1a690:", resolve_rip_va(image_base + 0x02e1a690))

# Let's check all property registrations in PropertyRegistration.Initialise (0x003e4f30) for:
# ScoutPlayerPrioritiesReference:
#   0x72692047 ('G ir'), 0x67393649 ('I69g'), 0x736a3232 ('22js'), 0x73735043 ('CPss')
# SpecificallyScoutedPersonReference:
#   0x706c7972 ('plyr'), 0x644d7861 ('axMd'), 0x63594545 ('EEYc'), 0x75446333 ('3cDu'),
#   0x71754c76 ('vLuq'), 0x73714e20 (' Nqs'), 0x6e475773 ('sWGn')

props = [
    ("ScoutPlayerPriorities.G_ir", 0x72692047),
    ("ScoutPlayerPriorities.I69g", 0x67393649),
    ("ScoutPlayerPriorities.SpecificallyScoutedPlayers ('22js')", 0x736a3232),
    ("ScoutPlayerPriorities.CPss", 0x73735043),
    ("SpecificallyScoutedPerson.Player ('plyr')", 0x706c7972),
    ("SpecificallyScoutedPerson.axMd", 0x644d7861),
    ("SpecificallyScoutedPerson.EEYc", 0x63594545),
    ("SpecificallyScoutedPerson.3cDu", 0x75446333),
    ("SpecificallyScoutedPerson.vLuq", 0x71754c76),
    ("SpecificallyScoutedPerson._Nqs", 0x73714e20),
    ("SpecificallyScoutedPerson.sWGn", 0x6e475773),
]

fn_start = rva_to_off(0x003e4f30)
fn_end = rva_to_off(rva_to_end.get(0x003e4f30, 0x00410000))

for label, val in props:
    pat = b"\xb9" + struct.pack("<I", val)
    pos = fn_start
    while True:
        idx = pe.find(pat, pos, fn_end)
        if idx == -1:
            break
        rva = off_to_rva(idx)
        print(f"\nFound {label} (0x{val:08x}) at RVA 0x{rva:08x}:")
        # scan next 120 bytes for RIP-relative loads (48 8b 05 / 4c 8b 05)
        sub = pe[idx:idx+130]
        for j in range(len(sub) - 7):
            if sub[j] in (0x48, 0x4c) and sub[j+1] == 0x8b and (sub[j+2] & 0xc7) == 0x05:
                rel = struct.unpack_from("<i", sub, j+3)[0]
                target_rva = rva + j + 7 + rel
                print(f"  +0x{j:02x}: RIP [0x{target_rva:08x}] -> {resolve_rip_va(image_base + target_rva)}")
        pos = idx + 1
