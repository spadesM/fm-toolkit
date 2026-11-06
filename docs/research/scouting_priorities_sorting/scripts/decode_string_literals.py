import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, sections, dump_func_details

print("Header ints:", [f"{i}:0x{x:x}" for i, x in enumerate(hdr[:36]) if x != 0])
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]

def get_str_literal(idx: int) -> str:
    if idx < 0 or idx * 8 >= str_lit_sz:
        return f"<oob:{idx}>"
    length, data_idx = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    raw = meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length]
    return raw.decode("utf-8", errors="replace")

# Let's check for known string literals in global-metadata.dat:
for i in range(str_lit_sz // 8):
    s = get_str_literal(i)
    if s in ("plyr", "J1Ct", "binding", "binding.", "#sort", "player", "Player", "SpecificallyScoutedPlayers", "ScoutPriorities"):
        print(f"  str_lit[{i}] (0x{i:x}, encoded_v29=0x{(5<<29)|i:08x}, encoded_v31=0x{(5<<29)|(i<<1):08x}, encoded_v31_1=0x{(5<<29)|(i<<1)|1:08x}) = {s!r}")

# Let's dump SetSorting_2 (0x015efce0) and SetupRow (0x015aa320) using dump_func_details
dump_func_details("StreamedTable.SetSorting_2", 0x015efce0)
dump_func_details("StreamedListView.SetupRow", 0x015aa320, 0x160)
