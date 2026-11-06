import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from find_scout_regs import pe, meta, hdr, image_base, va_to_off, off_to_va, dump_with_strings, get_mstr, get_str_literal

types_off, types_sz = hdr[40], hdr[41]
methods_off, methods_sz = hdr[32], hdr[33]
vtable_off, vtable_sz = hdr[36], hdr[37]

# 1. Dump 0x016abca0 and 0x016a9310
dump_with_strings("VirtualisedList_016abca0", 0x016abca0, 0x150)
dump_with_strings("VirtualisedList_016a9310", 0x016a9310, 0x150)

# 2. Check what [this + 0xd68], [this + 0xd98], [this + 0xda8], [this + 0xe18], [this + 0xeb8] are in StreamedListView / StreamedTable
# In Il2CppClass, vtable starts at offset 0x138!
# So vtable offset 0xd68 -> slot index (0xd68 - 0x138) // 16 = 0xc30 // 16 = 195!
for off in [0xd68, 0xd98, 0xda8, 0xe18, 0xeb8]:
    slot = (off - 0x138) // 16
    print(f"Il2CppClass offset 0x{off:x} -> vtable slot {slot}")

# Find TypeDefinitions for StreamedListView and StreamedTable
num_types = types_sz // 88
for tid in range(num_types):
    t_off = types_off + tid * 88
    name_idx, ns_idx = struct.unpack_from("<II", meta, t_off)
    name = get_mstr(name_idx)
    ns = get_mstr(ns_idx)
    if name in ("StreamedListView", "StreamedTable", "VirtualisedList") and "SI." in ns:
        vstart, vcount = struct.unpack_from("<IH", meta, t_off + 44) # wait let's check TypeDefinition layout
        print(f"Type[{tid}] {ns}.{name}")
        # Let's unpack all 22 ints of TypeDefinition
        fields = struct.unpack_from("<22I", meta, t_off)
        print("  fields:", fields)
