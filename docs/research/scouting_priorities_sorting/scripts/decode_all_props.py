import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import pe, meta, hdr, image_base, va_to_off, resolve_rip, get_mstr, dump_fast, types_off, types_sz, methods_off, methods_sz

def off_to_rva(foff):
    from dump_headers_fast import sections
    for _, vaddr, vsize, raddr, rsize in sections:
        if raddr <= foff < raddr + rsize:
            return vaddr + (foff - raddr)
    return 0

prop_ids = [
    # SpecificallyScoutedPersonReference (0x00696f80)
    (b"\xb9\x72\x79\x6c\x70", "SpecificallyScoutedPerson:plyr (0x706c7972)"),
    (b"\xb9\x61\x78\x4d\x64", "SpecificallyScoutedPerson:axMd (0x644d7861)"),
    (b"\xb9\x45\x45\x59\x63", "SpecificallyScoutedPerson:EEYc (0x63594545)"),
    (b"\xb9\x33\x63\x44\x75", "SpecificallyScoutedPerson:3cDu (0x75446333)"),
    (b"\xb9\x76\x4c\x75\x71", "SpecificallyScoutedPerson:vLuq (0x71754c76)"),
    (b"\xb9\x20\x4e\x71\x73", "SpecificallyScoutedPerson:_Nqs (0x73714e20)"),
    (b"\xb9\x73\x57\x47\x6e", "SpecificallyScoutedPerson:sWGn (0x6e475773)"),
    # SpecificallyScoutedTeamReference (0x006973d0)
    (b"\xb9\x6d\x61\x65\x54", "SpecificallyScoutedTeam:maeT (0x5465616d)"),
    # ScoutPlayerPrioritiesReference (0x0067d360)
    (b"\xb9\x47\x20\x69\x72", "ScoutPlayerPriorities:ri_G (0x72692047)"),
    (b"\xb9\x49\x36\x39\x67", "ScoutPlayerPriorities:g96I (0x67393649)"),
    (b"\xb9\x32\x32\x6a\x73", "ScoutPlayerPriorities:sj22 (0x736a3232)"),
    (b"\xb9\x43\x50\x73\x73", "ScoutPlayerPriorities:ssPC (0x73735043)"),
    # ScoutPlayerPriorities extra FourCCs in GetProperties/GetValue
    (b"\xb9\x59\x49\x6d\x31", "ScoutTeamPriorities:1mIY (0x316d4959)"),
    (b"\xb9\x70\x39\x79\x62", "ScoutTeamPriorities:by9p (0x62793970)"),
    (b"\xb9\x63\x61\x39\x68", "ScoutTeamPriorities:h9ac (0x68396163)"),
    (b"\xb9\x45\x35\x65\x78", "ScoutTeamPriorities:xe5E (0x78653545)"),
    (b"\xb9\x44\x62\x77\x69", "ScoutPlayerPrioritiesEvent:iwbD (0x69776244)"),
    (b"\xb9\x4b\x4c\x43\x53", "SpecificallyScoutedEvent:SCLK (0x53434c4b)"),
]

for pat, label in prop_ids:
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_rva(idx)
        if 0x003e4f30 <= rva <= 0x004c5d06:
            # Look FORWARD ~0x50..0x65 bytes for 4c 8b 05 (mov r8, [rip + disp])
            chunk = pe[idx : idx + 0x70]
            for i in range(0x40, len(chunk) - 7):
                if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
                    disp = struct.unpack_from("<i", chunk, i + 3)[0]
                    insn_rva = rva + i
                    tva = image_base + insn_rva + 7 + disp
                    print(f"{label:45s} at RVA 0x{rva:08x} -> {resolve_rip(tva)}")
        pos = idx + 1
