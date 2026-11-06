import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

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

def off_to_va(off: int) -> int:
    for _, vaddr, _, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return image_base + vaddr + (off - raddr)
    return 0

def va_to_off(va: int) -> int:
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            off = raddr + (rva - vaddr)
            return off if off < raddr + rsize else -2
    return -1

pdata_sec = [s for s in sections if s[0] == ".pdata"][0]
pdata = pe[pdata_sec[3] : pdata_sec[3] + pdata_sec[4]]
rva_to_end = {}
cur_start = None
for i in range(0, len(pdata), 12):
    b_rva, e_rva, u_rva = struct.unpack_from("<III", pdata, i)
    if b_rva == 0:
        continue
    u_off = va_to_off(image_base + u_rva)
    flags = (pe[u_off] >> 3) if u_off >= 0 else 0
    if (flags & 4) and cur_start is not None and b_rva == rva_to_end[cur_start]:
        rva_to_end[cur_start] = e_rva
    else:
        cur_start = b_rva
        rva_to_end[cur_start] = e_rva

rva = 0x00abdcc0
sz = rva_to_end.get(rva, rva + 800) - rva
print(f"=== SetSorting<T> (0x{rva:08x}, size={sz}) ===")
off = va_to_off(image_base + rva)
code = pe[off : off + sz]
for line_off in range(0, len(code), 16):
    chunk = code[line_off : line_off + 16]
    print(f"  +0x{line_off:03x}: {chunk.hex(' ')}")
