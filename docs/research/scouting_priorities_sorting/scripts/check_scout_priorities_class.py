import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va,
    dump_func_details, rva_to_end, get_mstr, methods_off, types_off, modules
)

# 1. Search for 32 32 6a 73 ('22js' = SpecificallyScoutedPlayers) and 48 61 37 76 ('Ha7v' = ScoutPriorities)
for name, pat in [("SpecificallyScoutedPlayers (22js)", b'\x32\x32\x6a\x73'), ("ScoutPriorities (Ha7v)", b'\x48\x61\x37\x76')]:
    print(f"=== Searching for {name} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            print(f"  Found at RVA 0x{rva:08x}")
            if rva not in (0x003f94ce, 0x003fdcb6):
                dump_func_details(f"Hit_{name}_0x{rva:08x}", rva - 0x60, 256)
        pos = idx + 1

# 2. List all methods of StreamedListView (Type 5791) and StreamedTable (Type 5967)
_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for tid, tname in [(5791, "StreamedListView"), (5967, "StreamedTable")]:
    tu = struct.unpack_from("<22i", meta, types_off + tid * 88)
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    vtable_start = tu[11]
    vtable_cnt = (tu[17] >> 16) & 0xFFFF
    print(f"\n=== Methods of {tname} (start={m_start}, count={m_cnt}, vtable_start={vtable_start}, vtable_cnt={vtable_cnt}) ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        slot = mu[10]
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
        rva = va - image_base if va else 0
        print(f"  Method {mi} ({mname}): slot={slot} RVA=0x{rva:08x}")
