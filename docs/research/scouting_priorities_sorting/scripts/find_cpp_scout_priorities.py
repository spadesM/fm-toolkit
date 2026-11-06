import sys
sys.path.insert(0, r"c:\Repos\fm26save")
from check_deep_sorting import dump_func_details, pe, meta, rva_to_end, va_to_off, off_to_va, image_base
import struct

# Find which RVA contains a given file offset
sorted_starts = sorted(rva_to_end.keys())
import bisect

def off_to_func_rva(foff):
    va = off_to_va(foff)
    if not va: return 0
    rva = va - image_base
    idx = bisect.bisect_right(sorted_starts, rva) - 1
    if idx >= 0:
        s = sorted_starts[idx]
        if s <= rva < rva_to_end[s]:
            return s
    return rva

fourccs = [
    ("SpecificallyScoutedPlayers? 0x73735043", b"\x43\x50\x73\x73"),
    ("SpecificallyScoutedPlayers? 0x736a3232", b"\x32\x32\x6a\x73"),
    ("SpecificallyScoutedPlayers? 0x72692047", b"\x47\x20\x69\x72"),
    ("ScoutPriorities prop 0x75446333", b"\x33\x63\x44\x75"),
    ("ScoutPriorities prop 0x71754c76", b"\x76\x4c\x75\x71"),
    ("ScoutPriorities prop 0x73714e20", b"\x20\x4e\x71\x73"),
    ("ScoutPriorities prop 0x6e475773", b"\x73\x57\x47\x6e"),
]

for label, pat in fourccs:
    pos = 0
    funcs = []
    while True:
        idx = pe.find(pat, pos)
        if idx == -1: break
        frva = off_to_func_rva(idx)
        funcs.append(f"off=0x{idx:x}->func=0x{frva:08x}")
        pos = idx + 1
    print(f"{label}: {funcs}")
