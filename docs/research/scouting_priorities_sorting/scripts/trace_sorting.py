import struct
import re
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[24], hdr[25]
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

# Map all method RVAs to (image, type_name, method_name)
fm_ui_str_off = pe.find(b"\x00FM.UI.dll\x00") + 1
fm_ui_mod_off = pe.find(struct.pack("<Q", off_to_va(fm_ui_str_off)))
ptr_in_array_off = pe.find(struct.pack("<Q", off_to_va(fm_ui_mod_off)))
start_arr = ptr_in_array_off
while start_arr >= 8:
    cand_va = struct.unpack_from("<Q", pe, start_arr - 8)[0]
    cand_off = va_to_off(cand_va)
    if cand_off > 0:
        name_off = va_to_off(struct.unpack_from("<Q", pe, cand_off)[0])
        if name_off > 0 and b".dll" in pe[name_off : name_off + 64]:
            start_arr -= 8
            continue
    break

modules = {}
cur = start_arr
while True:
    cand_va = struct.unpack_from("<Q", pe, cur)[0]
    cand_off = va_to_off(cand_va)
    if cand_off <= 0:
        break
    name_va, m_cnt, m_ptrs_va = struct.unpack_from("<QQQ", pe, cand_off)
    name_off = va_to_off(name_va)
    if name_off <= 0:
        break
    end = pe.find(b"\x00", name_off)
    mname = pe[name_off : end].decode("utf-8", errors="replace")
    if not (mname.endswith(".dll") or mname == "__Generated"):
        break
    modules[mname] = (cand_off, m_cnt, m_ptrs_va)
    cur += 8

rva_to_method_name = {}
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules:
        continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    if ptrs_off < 0 or m_cnt_mod == 0:
        continue
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            if 0 <= rid < m_cnt_mod:
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                if va > 0:
                    rva_to_method_name[va - image_base] = f"{tname}.{mname}"

# Also check usym symbol table for exact C++/IL2CPP function names!
usym_path = root / "GameAssembly.usym"
if not usym_path.exists():
    usym_path = root / "il2cpp.usym"

def inspect_func(label, rva, sz):
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    # Find all E8 / E9 relative calls/jumps
    for i in range(len(code) - 5):
        if code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            if target_rva in rva_to_method_name:
                op = "CALL" if code[i] == 0xE8 else "JMP"
                print(f"  +0x{i:03x}: {op} 0x{target_rva:08x} -> {rva_to_method_name[target_rva]}")
        # Also check struct field offsets [reg + 0x700..0xB00]
        if i + 6 <= len(code) and code[i] in (0x80, 0x83, 0x88, 0x89, 0x8A, 0x8B, 0x39, 0x3B):
            modrm = code[i + 1]
            if (modrm & 0xC0) == 0x80:
                disp = struct.unpack_from("<i", code, i + 2)[0]
                if 0x600 <= disp <= 0xB00:
                    print(f"  +0x{i:03x}: field access +0x{disp:03x} (bytes={code[max(0,i-2):i+7].hex(' ')})")

# Let's also list all methods of StreamedList / StreamedObjectList / BindableList (base classes of StreamedTable!)
for ti in range(5935, 5968):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if any(k in tname for k in ["Streamed", "List", "Table"]):
        print(f"Type {ti}: {tname}")
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        _, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
        ptrs_off = va_to_off(m_ptrs_va)
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
            if any(k in mname.lower() for k in ["sort", "slice", "reorder", "drag", "bind", "setlist"]):
                print(f"  {tname}.{mname}: RVA=0x{va - image_base if va else 0:08x}")

for name, rva, sz in [
    ("MakeColumnHeader", 0x015eac30, 973),
    ("CreateHeader", 0x015e8f00, 421),
    ("OnHeaderClicked", 0x015ec910, 600),
    ("SetSorting_2", 0x015efc40, 146),
    ("SetSorting_4", 0x015efce0, 653),
    ("UpdateSortColum", 0x015f1380, 322),
    ("TrySetColumnsAndSort", 0x015f0040, 494),
]:
    inspect_func(name, rva, sz)
