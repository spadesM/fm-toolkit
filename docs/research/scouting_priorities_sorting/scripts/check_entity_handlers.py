from check_deep_sorting import dump_func_details, meta, methods_off, get_mstr as get_str, data, rva_to_off
import struct

for m_idx in range(10924, 10937):
    m_off = methods_off + m_idx * 56
    rva, _, name_idx = struct.unpack_from("<III", meta, m_off)
    print(f"SpecificallyScoutedPersonReference.{get_str(name_idx)}: RVA=0x{rva:08x}")
    if get_str(name_idx) in ("GetPropertyTypeInternal", "AcceptsPropertyInternal", "GetPropertyDescriptionInternal"):
        dump_func_details(f"SpecificallyScoutedPersonReference.{get_str(name_idx)}", rva, 300)

# Search GameAssembly.dll for fourcc 'tC1J' (0x7443314a -> 4a 31 43 74) and 'A4yw' (0x41347977 -> 77 79 34 41)
for label, pat in [("tC1J (0x7443314a)", b"\x4a\x31\x43\x74"), ("A4yw (0x41347977)", b"\x77\x79\x34\x41")]:
    pos = 0
    hits = []
    while True:
        idx = data.find(pat, pos)
        if idx == -1: break
        hits.append(hex(idx))
        pos = idx + 1
    print(f"Hits for {label}: {hits[:30]} (total {len(hits)})")
