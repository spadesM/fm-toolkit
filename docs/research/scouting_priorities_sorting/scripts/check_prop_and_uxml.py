import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, types_off, types_sz, methods_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_end, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated
from compare_full_st_serialized_data import parse_bundle_with_reftypes

# 1. Search for 'J1Ct' (0x7443314a = b"J1Ct") or 'plyr' (0x706c7972 = b"rylp") in PropertyRegistration.Initialise (0x003fdc00)
prop_init_rva = 0x003fdc00
prop_init_end = rva_to_end.get(prop_init_rva, prop_init_rva + 0x200000)
prop_init_off = va_to_off(image_base + prop_init_rva)
prop_init_sz = prop_init_end - prop_init_rva
print(f"PropertyRegistration.Initialise: RVA=0x{prop_init_rva:08x}, size={prop_init_sz}")

chunk = pe[prop_init_off:prop_init_off + prop_init_sz]
for pat_name, pat in [("J1Ct (0x7443314a)", b"\x4a\x31\x43\x74"), ("plyr (0x706c7972)", b"\x72\x79\x6c\x70"), ("ScoutPlayerPriorities (0x44420069)", b"\x69\x00\x42\x44")]:
    pos = 0
    hits = []
    while True:
        idx = chunk.find(pat, pos)
        if idx < 0:
            break
        hits.append(prop_init_rva + idx)
        pos = idx + 1
    print(f"Pattern {pat_name}: {len(hits)} hits: {[hex(h) for h in hits[:20]]}")

# Wait: what if 'J1Ct' is in a sub-function called by PropertyRegistration.Initialise or anywhere in .text?
# Let's search the entire .text section for b"\x4a\x31\x43\x74" (0x7443314a = 'J1Ct')!
text_Hits = []
pos = 0
while True:
    idx = pe.find(b"\x4a\x31\x43\x74", pos)
    if idx < 0:
        break
    va = off_to_va(idx)
    if va:
        rva = va - image_base
        text_Hits.append(rva)
    pos = idx + 1
print(f"All PE hits for 'J1Ct' (0x7443314a): {[hex(h) for h in text_Hits]}")
for h in text_Hits:
    # find containing function
    best_fn = None
    for fn_rva, fn_end in rva_to_end.items():
        if fn_rva <= h < fn_end:
            best_fn = (fn_rva, fn_end)
            break
    if best_fn:
        fn_rva, fn_end = best_fn
        print(f"  Hit 0x{h:08x} in {rva_to_method_name.get(fn_rva, hex(fn_rva))} (0x{fn_rva:08x}..0x{fn_end:08x}, offset +0x{h-fn_rva:x})")
        # Dump 256 bytes around the hit!
        start_rva = max(fn_rva, h - 0x80)
        end_rva = min(fn_end, h + 0x180)
        dump_func_details(f"Around J1Ct hit 0x{h:08x}", start_rva, end_rva - start_rva)
