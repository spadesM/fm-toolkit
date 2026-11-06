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

for name, rva, sz in [
    ("get_DisableSorting", 0x015f2190, 32),
    ("set_DisableSorting", 0x015f2420, 32),
    ("get_DragCellID", 0x015f21a0, 32),
    ("get_IsDragCellActive", 0x015f2200, 64),
    ("OnHeaderClicked", 0x015ec910, 600),
    ("MakeColumnHeader", 0x015eac30, 973),
    ("SetSorting_2", 0x015efc40, 146),
    ("SetSorting_4", 0x015efce0, 653),
    ("UpdateSortColum", 0x015f1380, 322),
    ("TrySetColumnsAndSort", 0x015f0040, 494),
]:
    off = rva_to_off(rva)
    code = pe[off : off + sz]
    print(f"=== {name} (RVA=0x{rva:08x}) ===")
    print(code[:128].hex(" "))
