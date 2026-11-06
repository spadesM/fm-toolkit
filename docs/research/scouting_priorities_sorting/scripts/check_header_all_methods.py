import struct

DLL_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll"
META_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat"

with open(DLL_PATH, "rb") as f:
    pe = f.read()
with open(META_PATH, "rb") as f:
    meta = f.read()

e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
num_sections = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
image_base = struct.unpack_from("<Q", pe, e_lfanew + 24 + 24)[0]
sec_off = e_lfanew + 24 + opt_hdr_size
sections = []
for i in range(num_sections):
    s = sec_off + i * 40
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", pe, s + 8)
    sections.append((vaddr, vsize, raddr, rsize))

def va_to_off(va):
    rva = va - image_base
    for vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

def off_to_va(off):
    for vaddr, vsize, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return image_base + vaddr + (off - raddr)
    return 0

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(idx):
    if idx < 0 or idx >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + idx)
    return meta[str_off + idx : end].decode("utf-8", errors="replace")

# Check MethodDef 48974, 49029, 49031
for midx in (48974, 49029, 49031):
    mu = struct.unpack_from("<7i4H", meta, methods_off + midx * 36)
    tu = struct.unpack_from("<22i", meta, types_off + mu[1] * 88)
    print(f"MethodDef {midx}: {get_mstr(tu[0])}.{get_mstr(mu[0])} (token=0x{mu[6]&0xffffffff:08x}, declaringType={mu[1]})")
