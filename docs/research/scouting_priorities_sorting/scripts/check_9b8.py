import struct
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()

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

def rva_to_off(rva: int) -> int:
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

# Check UxmlSerializedData.Deserialize (RVA=0x015f36b0, size=2747)
off = rva_to_off(0x015f36b0)
code = pe[off : off + 2747]
# Search for 0x09b8 (b8 09 00 00) in Deserialize!
import re
for m in re.finditer(rb"\xb8\x09\x00\x00", code):
    pos = m.start()
    print(f"Found 0x9b8 at +{pos} (0x{pos:x}):", code[max(0, pos-32):min(len(code), pos+32)].hex(" "))

# Also search for all references to 0x9b8 across the entire StreamedTable region (0x015e5000..0x015f5000)
st_off = rva_to_off(0x015e5000)
st_code = pe[st_off : st_off + 0x10000]
for m in re.finditer(rb"\xb8\x09\x00\x00", st_code):
    pos = m.start()
    rva = 0x015e5000 + pos
    print(f"Ref to 0x9b8 at RVA=0x{rva:08x}: {st_code[max(0, pos-16):min(len(st_code), pos+16)].hex(' ')}")
