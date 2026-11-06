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
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(idx):
    if idx < 0 or idx >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + idx)
    return meta[str_off + idx : end].decode("utf-8", errors="replace")

lit_cnt = str_lit_sz // 8
literals = [
    meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length].decode("utf-8", errors="replace")
    for length, data_idx in (struct.unpack_from("<II", meta, str_lit_off + i * 8) for i in range(lit_cnt))
]

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
                    rva_to_method_name.setdefault(va - image_base, []).append(f"{tname}.{mname}")

def resolve_rip_va(va: int) -> str:
    foff = va_to_off(va)
    if foff < 0 or foff + 8 > len(pe):
        return ""
    val = struct.unpack_from("<I", pe, foff)[0]
    if (val & 1) == 1:
        tag = val >> 29
        idx = (val & 0x1FFFFFFF) >> 1
        if tag == 5 and 0 <= idx < len(literals):
            return f'STR "{literals[idx]}"'
        elif tag == 3 and 0 <= idx * 36 < methods_sz:
            mu = struct.unpack_from("<7i4H", meta, methods_off + idx * 36)
            if 0 <= mu[2] * 88 < types_sz:
                tu = struct.unpack_from("<22i", meta, types_off + mu[2] * 88)
                return f"MethodDef {get_mstr(tu[0])}.{get_mstr(mu[0])}"
        return f"MetaUsage(tag={tag}, idx={idx})"
    return ""

def dump_func(label, rva, sz):
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for line_off in range(0, len(code), 16):
        chunk = code[line_off : line_off + 16]
        print(f"  +0x{line_off:03x}: {chunk.hex(' ')}")
    print("  --- Annotations ---")
    for i in range(len(code)):
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            names = rva_to_method_name.get(target_rva, [])
            if names or (0x00500000 <= target_rva <= 0x02500000):
                op = "CALL" if code[i] == 0xE8 else "JMP"
                print(f"  +0x{i:03x}: {op} 0x{target_rva:08x} -> {', '.join(names[:4])}")
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            target_va = image_base + rva + i + 7 + disp
            info = resolve_rip_va(target_va)
            if info:
                print(f"  +0x{i:03x}: RIP [0x{target_va - image_base:08x}] -> {info}")

dump_func("StreamedTable.MakeColumnHeader (+0x190..+0x3cd)", 0x015eac30 + 0x190, 0x3cd - 0x190)
dump_func("StreamedListView.GetItemFromView", 0x015a5a10, 220)
dump_func("StreamedListView.GetItemFromSource", 0x015a59e0, 48)
dump_func("StreamedListView.OnBindItemInternal", 0x015a67d0, 450)
