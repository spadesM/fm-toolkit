import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_streamed_table_more import pe, meta, hdr, image_base, va_to_off, off_to_va, dump_with_strings, get_str_literal, str_lit_off, str_lit_sz

# 1. Search string literals for SpecificallyScoutedPlayers or ScoutPriorities
for idx in range(str_lit_sz // 8):
    s = get_str_literal(idx)
    if "SpecificallyScouted" in s or "ScoutPriorit" in s:
        print(f"str_lit[{idx}] = {s!r}")
        # Find metadata usage for this str_lit: tag=5 -> (5 << 29) | (idx << 1) | 1
        target_val = (5 << 29) | (idx << 1) | 1
        pat = struct.pack("<Q", target_val)
        pos = 0
        while True:
            found = pe.find(pat, pos)
            if found == -1:
                break
            data_rva = off_to_va(found) - image_base
            print(f"  data_rva = 0x{data_rva:08x}")
            pos = found + 1

# 2. Dump Header.Bind, Header.BindHintTooltip, Column..ctor, ApplyPersistedSortingState, 0x00292620
targets = [
    ("Header.Bind", 0x015df4f0, 0x4a0),
    ("Header.BindHintTooltip", 0x015df460, 0x90),
    ("Column..ctor", 0x015dee80, 0x200),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0, 0x350),
    ("Sub_00292620", 0x00292620, 0x100),
]
for label, rva, sz in targets:
    dump_with_strings(label, rva, sz)
