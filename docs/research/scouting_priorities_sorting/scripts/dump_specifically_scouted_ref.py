import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, dump_func_details, rva_to_method_name, va_to_off, image_base,
    types_off, types_sz, methods_off, get_mstr, hdr
)

dump_func_details("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0, 0x90)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80, 0x270)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200, 0x170)

# Search global-metadata strings or PE UTF-16 strings for SpecificallyScoutedPlayers and ScoutPriorities
for target in [b"SpecificallyScoutedPlayers", b"ScoutPriorities", b"SpecificallyScoutedPerson"]:
    u16 = target.decode().encode("utf-16le")
    idx = 0
    while True:
        idx = pe.find(u16, idx)
        if idx == -1:
            break
        print(f"Found UTF-16 {target.decode()} at PE offset 0x{idx:x}")
        idx += 2

# Also search metadata string literals!
lit_info_off, lit_info_sz = hdr[2], hdr[3]
lit_data_off, lit_data_sz = hdr[4], hdr[5]
cnt = lit_info_sz // 8
for i in range(cnt):
    length, d_off = struct.unpack_from("<II", meta, lit_info_off + i * 8)
    s = meta[lit_data_off + d_off : lit_data_off + d_off + length]
    if any(k in s.lower() for k in (b"specificallyscouted", b"scoutpriorities", b"scoutpriority")):
        print(f"String literal #{i}: {s.decode('utf-8', errors='replace')}")
