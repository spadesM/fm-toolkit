import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import pe, meta, methods_off, types_off, get_mstr, image_base, va_to_off, get_usym_dict, sections, dump_fast
from list_table_rvas import get_method_rva

# 1. Check all occurrences of 0x9b8 (b8 09 00 00) in StreamedTable (0x015df000..0x015f5000)
s_rva, e_rva = 0x015df000, 0x015f5000
off = va_to_off(image_base + s_rva)
chunk = pe[off : off + (e_rva - s_rva)]
print("=== Hits for 0x9b8 (DisableSorting) in StreamedTable ===")
pos = 0
while True:
    idx = chunk.find(b"\xb8\x09\x00\x00", pos)
    if idx < 0: break
    rva = s_rva + idx
    umap = get_usym_dict(rva - 6, 16)
    uinfo = ", ".join( next(iter(umap.values()), []) )
    print(f"  0x{rva:08x} ({uinfo})")
    pos = idx + 1

# 2. List RVAs of key StreamedTable methods
wanted = [
    48799, 48800, 48839, 48841, 48842, 48847, 48848,
    48869, 48870, 48871, 48872, 48873, 48874, 48876, 48877,
    48904, 48919, 48920, 48921, 48923, 48932, 48933, 48944
]
rva_list = []
for mi in range(48771, 48948):
    mname, rva = get_method_rva(mi)
    rva_list.append((rva, mi, mname))
rva_list.sort()

for idx_in_sorted, (rva, mi, mname) in enumerate(rva_list):
    if mi in wanted:
        next_rva = rva + 0x200
        for nrva, _, _ in rva_list[idx_in_sorted+1:]:
            if nrva > rva:
                next_rva = min(nrva, rva + 0x500)
                break
        dump_fast(f"StreamedTable.{mname} (mi={mi})", rva, next_rva)

# 3. Also dump VirtualisedList around 0x016a8500..0x016a8d00
dump_fast("VirtualisedList (0x016a8500..0x016a8d00)", 0x016a8500, 0x016a8d00)
