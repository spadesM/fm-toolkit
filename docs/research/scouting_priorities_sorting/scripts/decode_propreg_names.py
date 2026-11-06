import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, va_to_off, image_base, dump_func_details

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz, str_lit_data_off, str_lit_data_sz = hdr[2], hdr[3], hdr[4], hdr[5]
def get_str_lit(idx):
    ln, doff = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    return meta[str_lit_data_off + doff : str_lit_data_off + doff + ln].decode("utf-8", errors="replace")

hits = [
    ("ScoutPlayerPrioritiesReference: 0x72692047 ('G ir')", 0x478164),
    ("ScoutPlayerPrioritiesReference: 0x67393649 ('I69g')", 0x4683e0),
    ("ScoutPlayerPrioritiesReference: 0x736a3232 ('22js')", 0x3fdcb6),
    ("ScoutPlayerPrioritiesReference: 0x73735043 ('CPss')", 0x3fdc40),
    ("SpecificallyScoutedPersonReference: 0x706c7972 ('rylp')", 0x46ede4),
    ("SpecificallyScoutedPersonReference: 0x644d7861 ('axMd')", 0x46b096),
    ("SpecificallyScoutedPersonReference: 0x63594545 ('EEYc')", 0x46cb52),
    ("SpecificallyScoutedPersonReference: 0x75446333 ('3cDu')", 0x468d8e),
    ("SpecificallyScoutedPersonReference: 0x71754c76 ('vLuq')", 0x468ca2),
    ("SpecificallyScoutedPersonReference: 0x73714e20 (' Nqs')", 0x468c2c),
    ("SpecificallyScoutedPersonReference: 0x6e475773 ('sWGn')", 0x468bb6),
]

for label, rva in hits:
    off = va_to_off(image_base + rva)
    chunk = pe[off : off + 0x80]
    idx = chunk.find(b"\x4c\x8b\x05")
    if idx != -1:
        disp = struct.unpack_from("<i", chunk, idx + 3)[0]
        target_rva = rva + idx + 7 + disp
        val = struct.unpack_from("<Q", pe, va_to_off(image_base + target_rva))[0]
        lit_idx = (val & 0x1fffffff) >> 1
        print(f"{label} -> {get_str_lit(lit_idx)!r} (lit_idx={lit_idx})")

print("\nNow dumping SetupRow, HasReceived, ResetIndices, UpdateEnabledState:")
for name, rva in [
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320),
    ("SortData.HasReceived", 0x015a4040),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.UpdateEnabledState", 0x015aab80),
]:
    dump_func_details(name, rva)
