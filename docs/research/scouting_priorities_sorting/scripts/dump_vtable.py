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
vtable_methods_off, vtable_methods_sz = hdr[46], hdr[47]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz: return ""
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
        if raddr <= off < raddr + rsize: return image_base + vaddr + (off - raddr)
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
    if cand_off <= 0: break
    name_va, m_cnt, m_ptrs_va = struct.unpack_from("<QQQ", pe, cand_off)
    name_off = va_to_off(name_va)
    if name_off <= 0: break
    end = pe.find(b"\x00", name_off)
    mname = pe[name_off : end].decode("utf-8", errors="replace")
    if not (mname.endswith(".dll") or mname == "__Generated"): break
    modules[mname] = (cand_off, m_cnt, m_ptrs_va)
    cur += 8

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules: continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        tns = get_mstr(tu[1])
        if tname in ("StreamedListView", "StreamedTable", "ScoutPriorities", "SpecificallyScoutedPerson"):
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"\n=== {tns}.{tname} ({iname}, ti={ti}) ===")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = (va - image_base) if va > 0 else 0
                slot = mu[10]
                print(f"  [mi={mi}] 0x{rva:08x} (slot={slot}, voff=0x{0x138+slot*16:04x}): {mname}")
