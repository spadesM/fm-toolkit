import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

pe = dhf.pe

def off_to_rva(off):
    for _, vaddr, vsize, raddr, rsize in dhf.sections:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return 0

for label, val in [("SpecificallyScoutedPerson (tC1J)", 0x7443314a), ("ScoutPlayerPriorities (A4yw)", 0x41347977), ("SpecificallyScoutedTeam (SCLK)", 0x53434c4b)]:
    pat = struct.pack("<I", val)
    pos = 0
    print(f"=== Search for {label} (0x{val:08x}) ===")
    while True:
        idx = pe.find(pat, pos)
        if idx == -1: break
        pos = idx + 1
        rva = off_to_rva(idx)
        umap = dhf.get_usym_dict(rva - 64, 128)
        uinfo = []
        for k in sorted(umap.keys()):
            uinfo.extend(umap[k])
        print(f"  Hit at RVA 0x{rva:08x} (nearby usym: {uinfo[:5]})")
