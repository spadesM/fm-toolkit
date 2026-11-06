import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
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

def va_to_off(va: int) -> int:
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            off = raddr + (rva - vaddr)
            return off if off < raddr + rsize else -2
    return -1

# Also check if Zydis / distorm3 / iced_x86 / pefile is installed, or write a clean x86-64 disassembler for our functions
for mod in ["capstone", "iced_x86", "zydis", "distorm3"]:
    try:
        __import__(mod)
        print(f"Module {mod} is installed!")
    except ImportError:
        pass

# Check what is at StreamedListView.Reorderable!
# Earlier we saw StreamedListView.set_Reorderable (0x015ad4f0):
# 48 8b 81 78 07 00 00   mov rax, [rcx + 0x778] (<ListElement>k__BackingField!)
# 48 85 c0               test rax, rax
# 74 0b                  je +0x17
# 88 90 c1 05 00 00      mov [rax + 0x5c1], dl
# WAIT A SECOND! What is <ListElement>k__BackingField ([this + 0x778])?!
# Let's check the type of <ListElement>k__BackingField in StreamedListView!
tu = struct.unpack_from("<22i", meta, types_off + 5791 * 88)
f_start = tu[8]
f_cnt = tu[17] & 0xFFFF
print("StreamedListView fields around 63 (<ListElement>k__BackingField):")
for fi in range(f_start + 55, f_start + f_cnt):
    name_idx, type_idx = struct.unpack_from("<2i", meta, hdr[24] + fi * 12)
    print(f"  [{fi - f_start}] {get_mstr(name_idx)} (type_idx={type_idx})")
