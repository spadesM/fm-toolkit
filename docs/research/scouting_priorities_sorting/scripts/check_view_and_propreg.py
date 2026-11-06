import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr
from annotate_sorting_usym import dump_annotated

def rva_to_off(rva): return va_to_off(image_base + rva)
def off_to_rva(off): return off_to_va(off) - image_base

# 1. Dump StreamedTableView..ctor, StreamedTableView.Equals, StreamedTableViewSettingsCollection.GetTableView
for name, rva in [
    ("StreamedTableView..ctor", 0x01621e40),
    ("StreamedTableView.Equals", 0x01621500),
    ("StreamedTableViewSettingsCollection.GetTableView", 0x01620240),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)

# 2. Check what getter is registered for 0x736a3232 ('22js' = SpecificallyScoutedPlayers) at 0x003fdcb0..0x003fdd25
# Notice at 0x003fdcd3: 48 8b 05 b5 e1 9f 02 (mov rax, [rip + 0x029fe1b5])
# and at 0x003fdd0f: 4c 8b 05 7a c9 a1 02 (mov r8, [rip + 0x02a1c97a])
# and calls 0x002a5ed0! Let's check 0x002a5ed0!
dump_func_details("func_0x002a5ed0", 0x002a5ed0)

# Let's check what 0x00001d10 does!
dump_func_details("func_0x00001d10", 0x00001d10)
