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
fields_off, fields_sz = hdr[24], hdr[25]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

# Print all fields with their offsets for StreamedListView (5791), Header (5951), StreamedTable (5967), RowData
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

def dump_func_details(label, rva, sz):
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    # Print hex in 16-byte lines AND annotate calls/jumps
    for line_off in range(0, len(code), 16):
        chunk = code[line_off : line_off + 16]
        print(f"  +0x{line_off:03x}: {chunk.hex(' ')}")
    print("  --- Annotations ---")
    for i in range(len(code) - 5):
        if code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            names = rva_to_method_name.get(target_rva, [])
            if names or (0x01400000 <= target_rva <= 0x01700000):
                op = "CALL" if code[i] == 0xE8 else "JMP"
                print(f"  +0x{i:03x}: {op} 0x{target_rva:08x} -> {', '.join(names[:4])}")
        if code[i] == 0x0F and code[i+1] in range(0x80, 0x90):
            disp = struct.unpack_from("<i", code, i + 2)[0]
            target_off = i + 6 + disp
            if 0 <= target_off <= sz:
                jcc = ["JO","JNO","JB","JAE","JE","JNE","JBE","JA","JS","JNS","JP","JNP","JL","JGE","JLE","JG"][code[i+1]-0x80]
                print(f"  +0x{i:03x}: {jcc} -> +0x{target_off:03x}")
        elif code[i] in range(0x70, 0x80):
            disp = struct.unpack_from("<b", code, i + 1)[0]
            target_off = i + 2 + disp
            if 0 <= target_off <= sz:
                jcc = ["JO","JNO","JB","JAE","JE","JNE","JBE","JA","JS","JNS","JP","JNP","JL","JGE","JLE","JG"][code[i]-0x70]
                print(f"  +0x{i:03x}: {jcc} (short) -> +0x{target_off:03x}")

for name, rva, sz in [
    ("StreamedTable.MakeColumnHeader", 0x015eac30, 973),
    ("StreamedTable.OnHeaderClicked", 0x015ec910, 600),
    ("StreamedTable.SetSorting_2", 0x015efc40, 146),
    ("StreamedTable.SetSorting_4", 0x015efce0, 653),
    ("StreamedListView.SetSortingBinding_2", 0x015a9a80, 83),
    ("StreamedListView.SetSortingBinding_3", 0x015a9ae0, 310),
    ("StreamedListView.HasSorting", 0x015a5f20, 218),
    ("StreamedListView.ApplySorting", 0x015a4260, 1208),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 509),
    ("StreamedListView.StateChanged", 0x015a9c80, 599),
]:
    dump_func_details(name, rva, sz)
