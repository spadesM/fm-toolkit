import sys
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
import struct

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[24], hdr[25]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(off):
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

def off_to_va(off):
    for _, vaddr, _, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return image_base + vaddr + (off - raddr)
    return 0

def va_to_off(va):
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

pdata_sec = [s for s in sections if s[0] == ".pdata"][0]
pdata = pe[pdata_sec[3] : pdata_sec[3] + pdata_sec[4]]
rva_to_end = {}
cur_start = None
for i in range(0, len(pdata), 12):
    b_rva, e_rva, u_rva = struct.unpack_from("<III", pdata, i)
    if b_rva == 0: continue
    u_off = va_to_off(image_base + u_rva)
    flags = (pe[u_off] >> 3) if u_off >= 0 else 0
    if (flags & 4) and cur_start is not None and b_rva == rva_to_end[cur_start]:
        rva_to_end[cur_start] = e_rva
    else:
        cur_start = b_rva
        rva_to_end[cur_start] = e_rva

# Find SI.Bindable.dll module
si_str_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
si_mod_off = pe.find(struct.pack("<Q", off_to_va(si_str_off)))
name_va, m_cnt_mod, m_ptrs_va = struct.unpack_from("<QQQ", pe, si_mod_off)
ptrs_off = va_to_off(m_ptrs_va)

# Find StreamedListView and StreamedTable types in SI.Bindable.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    if get_mstr(iu[0]) == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("StreamedListView", "StreamedTable", "Header", "Column", "StreamedTableFactory"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                print(f"\n=== {tname} (Type {ti}, {m_cnt} methods) ===")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    if 0 <= rid < m_cnt_mod:
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                        if va:
                            rva = va - image_base
                            end_rva = rva_to_end.get(rva, rva + 64)
                            foff = va_to_off(va)
                            mcode = pe[foff : foff + (end_rva - rva)]
                            tags = []
                            if b"\x68\x05\x00\x00" in mcode: tags.append("m_sortedIndices(+0x568)")
                            if b"\x38\x07\x00\x00" in mcode: tags.append("m_sortSpecifiers(+0x738)")
                            if b"\xd8\x07\x00\x00" in mcode: tags.append("Reorderable(+0x7d8)")
                            if b"\xb8\x09\x00\x00" in mcode: tags.append("DisableSorting(+0x9b8)")
                            if b"\x88\x09\x00\x00" in mcode: tags.append("m_factory(+0x988)")
                            if b"\xa0\x09\x00\x00" in mcode: tags.append("SortBinding(+0x9a0)")
                            if b"\xb0\x09\x00\x00" in mcode: tags.append("DefaultSortColumn(+0x9b0)")
                            if tags or "Sort" in mname or "Reorder" in mname or "Drag" in mname or "Column" in mname:
                                print(f"  {mname} (RVA=0x{rva:08x}, sz={end_rva-rva}): {', '.join(tags)}")
