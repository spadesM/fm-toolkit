import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as d

# 1. Search string literals in global-metadata.dat for SpecificallyScouted, ScoutPriorities, J1Ct, etc.
print("=== 1. String Literals in global-metadata.dat ===")
num_lits = d.str_lit_sz // 8
for idx in range(num_lits):
    s = d.get_lit(idx)
    sl = s.lower()
    if any(k in sl for k in ["specificallyscouted", "scoutpriorit", "positioncombined", "overallreportgrade", "transfervaluerange", "playerstatus", "sortbinding", "disablesorting"]):
        print(f"  lit[{idx}] = {s!r}")

# 2. Check USYM for FM.GamePlugin.AutogenBindings.cs or SpecificallyScouted
print("\n=== 2. USYM Symbols matching SpecificallyScouted / ScoutPriorities ===")
for idx in range(d.sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", d.udata, d.records_off + idx * 24)
    if sym_off > 0:
        sym = d.get_ustr(sym_off)
        if any(k in sym.lower() for k in ["specificallyscouted", "scoutpriorit", "streamedtable", "streamedlistview"]):
            fn = d.get_ustr(file_off).split("/")[-1].split("\\")[-1]
            print(f"  0x{rva:08x} {sym} ({fn}:{line})")

# 3. Also check where fourcc 'J1Ct' (0x7443314A = 1950560586) appears in GameAssembly.dll!
print("\n=== 3. Occurrences of fourcc 'J1Ct' (0x7443314A) in GameAssembly.dll ===")
pat = struct.pack("<I", 1950560586)
pos = 0
while True:
    idx = d.pe.find(pat, pos)
    if idx < 0:
        break
    # convert file offset to RVA
    for name, vaddr, vsize, raddr, rsize in d.sections:
        if raddr <= idx < raddr + rsize:
            rva = vaddr + (idx - raddr)
            umap = d.get_usym_dict(rva - 0x100, 0x200)
            nearest = sorted(umap.items())[-1] if umap else (0, [])
            print(f"  FileOff=0x{idx:08x} RVA=0x{rva:08x} sec={name} nearest={nearest}")
    pos = idx + 1
