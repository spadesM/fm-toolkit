import sys
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, fourcc_to_ascii
import struct

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

# Search GameAssembly.dll for fourcc 'tC1J' (0x7443314a -> 4a 31 43 74) and 'A4yw' (0x41347977 -> 77 79 34 41)
for label, pat in [("tC1J (0x7443314a)", b"\x4a\x31\x43\x74"), ("A4yw (0x41347977)", b"\x77\x79\x34\x41")]:
    pos = 0
    hits = []
    while True:
        idx = pe.find(pat, pos)
        if idx == -1: break
        hits.append(hex(idx))
        pos = idx + 1
    print(f"Hits for {label}: {hits[:30]} (total {len(hits)})")

# Also check il2cpp.usym for StreamedTable / StreamedListView / ScoutPriorities
usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
if usym_path.exists():
    u = usym_path.read_bytes()
    magic, version, sym_count = struct.unpack_from("<4sII", u, 0)
    str_off = 24 + sym_count * 24
    print(f"usym count: {sym_count}, str_off: {str_off}")
    def get_ustr(off):
        if off <= 0 or str_off + off >= len(u): return ""
        end = u.find(b"\x00", str_off + off)
        return u[str_off + off : end].decode("utf-8", errors="replace")
    
    # Check symbols around RVA 0x015a0000..0x015f5000
    for i in range(sym_count):
        rva, name_o, file_o, line, _, _ = struct.unpack_from("<IIIIII", u, 24 + i * 24)
        if 0x015a3c00 <= rva <= 0x015ab000 or 0x015e5000 <= rva <= 0x015f2000:
            nm = get_ustr(name_o)
            fl = get_ustr(file_o)
            if "Sort" in nm or "Reorder" in nm or "Drag" in nm or "Header" in nm or "Column" in nm:
                print(f"  RVA=0x{rva:08x} line={line:4d} {nm} ({fl.split('/')[-1].split(chr(92))[-1]})")
