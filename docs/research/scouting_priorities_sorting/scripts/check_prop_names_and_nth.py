import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va

print("=== 1. Exact property names for ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference ===")
fourccs = [
    # ScoutPlayerPrioritiesReference (0x0067d360)
    (0x72692047, "ScoutPlayerPrioritiesReference"),
    (0x67393649, "ScoutPlayerPrioritiesReference"),
    (0x736a3232, "ScoutPlayerPrioritiesReference"),
    (0x73735043, "ScoutPlayerPrioritiesReference"),
    # SpecificallyScoutedPersonReference (0x00696f80)
    (0x706c7972, "SpecificallyScoutedPersonReference"),
    (0x644d7861, "SpecificallyScoutedPersonReference"),
    (0x63594545, "SpecificallyScoutedPersonReference"),
    (0x75446333, "SpecificallyScoutedPersonReference"),
    (0x71754c76, "SpecificallyScoutedPersonReference"),
    (0x73714e20, "SpecificallyScoutedPersonReference"),
    (0x6e475773, "SpecificallyScoutedPersonReference"),
]

for fcc, owner in fourccs:
    pat = b'\xb9' + struct.pack('<I', fcc)
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003c0000 <= rva <= 0x004c0000:
            # Look +0x40..+0x70 after idx for RIP-relative string literal
            strs = []
            for s_off in range(idx, idx + 0x70):
                if pe[s_off:s_off+3] in (b'\x48\x8b\x05', b'\x48\x8b\x0d', b'\x48\x8b\x15', b'\x4c\x8b\x05', b'\x4c\x8b\x0d'):
                    disp = struct.unpack_from('<i', pe, s_off + 3)[0]
                    target_va = off_to_va(s_off) + 7 + disp
                    info = resolve_rip_va(target_va)
                    if info and 'STR' in info:
                        strs.append((s_off - idx, info))
            print(f"  [{owner}] FourCC 0x{fcc:08x} ({struct.pack('<I', fcc)!r}) at 0x{rva:08x} -> {strs}")
        pos = idx + 1

print("\n=== 2. Dump Bindings.GetNthProperty (0x014c1450) full bytes and annotations ===")
dump_func_details("Bindings.GetNthProperty", 0x014c1450, rva_to_end.get(0x014c1450, 0x014c1670) - 0x014c1450)
