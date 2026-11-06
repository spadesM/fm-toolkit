import sys, os, glob
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name

with open("sorting_disasm17.txt", "w", encoding="utf-8") as f:
    sys.stdout = f

    # 1. Disassemble Bindings.Set implementation at 0x014c3770
    rva = 0x014c3770
    end_rva = rva_to_end.get(rva, rva + 0x600)
    dump_fast("Bindings.Set_impl (0x014c3770)", rva, min(end_rva, rva + 0x1000))

    # 2. Disassemble Bindings.SetValueOnNode / 0x014c6590 / 0x014d1c30
    for name, r in [
        ("Bindings_0x014c6590", 0x014c6590),
        ("Bindings_0x014d1c30", 0x014d1c30),
        ("StreamedListView_0x015aab80", 0x015aab80),
        ("StreamedTable_0x015a5d00", 0x015a5d00),
        ("StreamedTable_0x015a5b90", 0x015a5b90),
    ]:
        er = rva_to_end.get(r, r + 0x300)
        dump_fast(name, r, min(er, r + 0x1000))

    # 3. Search for byte patterns c1 05 00 00 (+0x5c1) and c1 04 00 00 (+0x4c1) in StreamedListView / StreamedTable range (0x01590000..0x01610000)
    start_off = va_to_off(image_base + 0x01590000)
    end_off = va_to_off(image_base + 0x01610000)
    chunk = pe[start_off:end_off]
    for pat_name, pat in [("+0x5c1", b"\xc1\x05\x00\x00"), ("+0x4c1", b"\xc1\x04\x00\x00"), ("+0x604", b"\x04\x06\x00\x00"), ("+0x605", b"\x05\x06\x00\x00")]:
        print(f"\n=== Occurrences of {pat_name} in 0x01590000..0x01610000 ===")
        idx = 0
        while True:
            pos = chunk.find(pat, idx)
            if pos == -1:
                break
            hit_rva = 0x01590000 + pos
            # find containing method
            best_m = None
            for mrva, mend in rva_to_end.items():
                if mrva <= hit_rva < mend:
                    best_m = (mrva, mend, rva_to_method_name.get(mrva, f"0x{mrva:08x}"))
                    break
            print(f"  RVA 0x{hit_rva:08x} in {best_m}")
            idx = pos + 1
