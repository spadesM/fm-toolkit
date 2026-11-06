import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()
hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]
genspec_off, genspec_sz = hdr[54], hdr[55]

def get_mstr(off):
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

# Find Il2CppMetadataRegistration to resolve Il2CppType indices (tag 1 and tag 2) and MethodSpecs (tag 6)
# Let's check what functions are at 0x00af20c0, 0x00afe080, 0x00aec0b0, 0x014c5740, 0x00a5bbf0
e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
num_sec = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
image_base = struct.unpack_from("<Q", pe, e_lfanew + 24 + 24)[0]
sec_off = e_lfanew + 24 + opt_size
sections = []
for i in range(num_sec):
    s = pe[sec_off + i * 40 : sec_off + (i + 1) * 40]
    name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
    sections.append((name, vaddr, vsize, raddr, rsize))

def va_to_off(va):
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

# Let's check USYM for 0x00af20c0, 0x00afe080, 0x00aec0b0, 0x014c5740, 0x014bee30
usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
udata = usym_path.read_bytes()
_, _, sym_count, _, _, _ = struct.unpack_from("<4sIIIII", udata, 0)
records_off = 24
str_table_off = records_off + sym_count * 24
str_blob = udata[str_table_off:]
def get_ustr(off):
    if off <= 0 or off >= len(str_blob): return ""
    return str_blob[off:str_blob.find(b"\x00", off)].decode("utf-8", errors="replace")

# Binary search in usym records by RVA! (records are sorted by RVA!)
def lookup_usym(target_rva, span=0x500):
    lo, hi = 0, sym_count - 1
    while lo < hi:
        mid = (lo + hi) // 2
        rva = struct.unpack_from("<I", udata, records_off + mid * 24)[0]
        if rva < target_rva:
            lo = mid + 1
        else:
            hi = mid
    res = []
    for idx in range(max(0, lo - 5), min(sym_count, lo + 200)):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
        if rva > target_rva + span:
            break
        if rva >= target_rva - 0x20:
            p_sym = ""
            if 0 <= parent_idx < sym_count:
                _, _, ps_off, pf_off, _, _ = struct.unpack_from("<IIIIII", udata, records_off + parent_idx * 24)
                p_sym = get_ustr(ps_off)
            res.append((rva - target_rva, p_sym, get_ustr(sym_off), get_ustr(file_off), line))
    return res

for name, rva, sz in [
    ("sub_00af20c0", 0x00af20c0, 1188),
    ("sub_00afe080", 0x00afe080, 300),
    ("sub_00aec0b0", 0x00aec0b0, 300),
    ("Bindings.Set_014c5740", 0x014c5740, 400),
    ("Bindings.Bind_014bee30", 0x014bee30, 400),
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 900),
]:
    print(f"=== {name} (0x{rva:08x}) ===")
    for rel, psym, sym, fn, ln in lookup_usym(rva, sz):
        short_fn = fn.split("/")[-1].split("\\")[-1] if fn else ""
        print(f"  +0x{rel:03x}: {psym} | {sym} ({short_fn}:{ln})")
