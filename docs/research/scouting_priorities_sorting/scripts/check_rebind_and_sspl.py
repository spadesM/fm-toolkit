import struct
from check_deep_sorting import pe, meta, hdr, types_off, types_sz, methods_off, fields_off, get_mstr, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
from annotate_sorting_usym import dump_annotated

targets = [
    ("StreamedTable.OnRebindItem", 0x015ed7d0),
    ("StreamedListView.OnRebindItemInternal", 0x015a7660),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("VirtualisationController.Refresh", 0x016a52b0),
    ("VirtualisationController.CalculateView", 0x016a40a0),
    ("VirtualisedList.set_DynamicElements", 0x016aba90),
    ("VirtualisedList.set_Reorderable", 0x014dada0),
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x0067dc20),
]

for name, rva in targets:
    end_rva = rva_to_end.get(rva, rva + 0x400)
    dump_func_details(name, rva, min(end_rva - rva, 0x600))
    dump_annotated(name, rva)

# Also search for 'sSPl' (0x6c505373) and 'J1Ct' (0x7443314a) in pe
for tag_name, pat in [("sSPl (0x6c505373)", b"\x73\x53\x50\x6c"), ("J1Ct (0x7443314a)", b"\x4a\x31\x43\x74")]:
    print(f"\n=== Occurrences of {tag_name} ===")
    pos = 0
    hits = []
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = off_to_va(idx)
        rva = va - image_base if va else None
        hits.append((idx, rva))
        pos = idx + 1
    print(f"Total hits: {len(hits)}")
    for idx, rva in hits[:30]:
        print(f"  off=0x{idx:x}, rva=0x{rva:08x}" if rva else f"  off=0x{idx:x}")
        if rva and 0x1000 <= rva < 0x0c000000:
            # Find enclosing function or dump around rva-0x40
            start = max(0x1000, (rva - 0x40) & ~0xf)
            dump_func_details(f"Hit_{tag_name}_at_0x{rva:08x}", start, 0xc0)
