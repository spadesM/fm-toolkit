import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va,
    dump_func_details, rva_to_end, get_mstr
)
from find_scout_regs import resolve_data_rva

# 1. Dump StateChanged, Refresh, RefreshInternal, ClearSortingState, SetNoSorting
for name, rva in [
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.Refresh", 0x015a9390),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedListView.ClearSortingState", 0x015a5180),
    ("StreamedListView.SetNoSorting", 0x015a99d0),
    ("StreamedTable.SetNoSorting", 0x015ef750),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedListView.SetList", 0x015a9880),
]:
    dump_func_details(name, rva)

# 2. Search for the 7 FourCCs of SpecificallyScoutedPersonReference and 4 FourCCs of ScoutPlayerPrioritiesReference
fourccs = [
    ("rylp", b"\x72\x79\x6c\x70"),
    ("axMd", b"\x61\x78\x4d\x64"),
    ("EEYc", b"\x45\x45\x59\x63"),
    ("3cDu", b"\x33\x63\x44\x75"),
    ("vLuq", b"\x76\x4c\x75\x71"),
    (" Nqs", b"\x20\x4e\x71\x73"),
    ("sWGn", b"\x73\x57\x47\x6e"),
    ("tC1J (SpecificallyScoutedPerson)", b"\x4a\x31\x43\x74"),
]

for label, pat in fourccs:
    print(f"\n=== Searching for FourCC {label} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            print(f"  Found at RVA 0x{rva:08x}")
            if 0x003e0000 <= rva <= 0x00420000:
                # Print surrounding RIP references
                for off_delta in range(-32, 128):
                    cur = idx + off_delta
                    if pe[cur:cur+3] == b"\x4c\x8b\x05":
                        disp = struct.unpack_from("<i", pe, cur + 3)[0]
                        target_rva = (rva + off_delta) + 7 + disp
                        print(f"    +{off_delta}: RIP -> 0x{target_rva:08x} ({resolve_data_rva(target_rva)})")
        pos = idx + 1
