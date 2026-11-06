import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_j1ct_and_nth_prop import dump_with_strings, resolve_data_rva
from check_deep_sorting import pe, image_base, va_to_off, off_to_va

prop_ids = [
    (b"\xb9\x72\x79\x6c\x70", "J1Ct:plyr (0x706c7972)"),
    (b"\xb9\x61\x78\x4d\x64", "J1Ct:axMd (0x644d7861)"),
    (b"\xb9\x45\x45\x59\x63", "J1Ct:EEYc (0x63594545)"),
    (b"\xb9\x33\x63\x44\x75", "J1Ct:3cDu (0x75446333)"),
    (b"\xb9\x76\x4c\x75\x71", "J1Ct:vLuq (0x71754c76)"),
    (b"\xb9\x20\x4e\x71\x73", "J1Ct:_Nqs (0x73714e20)"),
    (b"\xb9\x73\x57\x47\x6e", "J1Ct:sWGn (0x6e475773)"),
    (b"\xb9\x47\x20\x69\x72", "ao3d:ri_G (0x72692047)"),
    (b"\xb9\x49\x36\x39\x67", "ao3d:g96I (0x67393649)"),
    (b"\xb9\x32\x32\x6a\x73", "ao3d:sj22 (0x736a3232)"),
    (b"\xb9\x43\x50\x73\x73", "ao3d:ssPC (0x73735043)"),
]

for pat, label in prop_ids:
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003e4f30 <= rva <= 0x004c5d06:
            # Look backwards ~40 bytes for 4c 8b 05 (mov r8, [rip + disp])
            chunk = pe[idx - 48 : idx + 16]
            for i in range(len(chunk) - 7):
                if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
                    disp = struct.unpack_from("<i", chunk, i + 3)[0]
                    insn_rva = rva - 48 + i
                    trva = insn_rva + 7 + disp
                    print(f"{label:28s} at RVA 0x{rva:08x} -> {resolve_data_rva(trva)}")
        pos = idx + 1

dump_with_strings("Bindings.GetNthProperty (full)", 0x014c1450)
