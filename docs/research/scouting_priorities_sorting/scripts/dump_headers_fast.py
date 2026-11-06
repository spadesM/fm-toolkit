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

def get_mstr(off):
    if off < 0 or off >= str_sz: return ""
    return meta[str_off + off : meta.find(b"\x00", str_off + off)].decode("utf-8", errors="replace")

def get_lit(idx):
    if 0 <= idx * 8 < str_lit_sz:
        l, d = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
        return meta[str_lit_data_off + d : str_lit_data_off + d + l].decode("utf-8", errors="replace")
    return ""

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

def va_to_off(va):
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
udata = usym_path.read_bytes()
_, _, sym_count, _, _, _ = struct.unpack_from("<4sIIIII", udata, 0)
records_off = 24
str_table_off = records_off + sym_count * 24
str_blob = udata[str_table_off:]
def get_ustr(off):
    if off <= 0 or off >= len(str_blob): return ""
    return str_blob[off:str_blob.find(b"\x00", off)].decode("utf-8", errors="replace")

def get_usym_dict(target_rva, span):
    lo, hi = 0, sym_count - 1
    while lo < hi:
        mid = (lo + hi) // 2
        rva = struct.unpack_from("<I", udata, records_off + mid * 24)[0]
        if rva < target_rva: lo = mid + 1
        else: hi = mid
    res = {}
    for idx in range(max(0, lo - 2), min(sym_count, lo + 300)):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
        if rva > target_rva + span: break
        if rva >= target_rva:
            fn = get_ustr(file_off).split("/")[-1].split("\\")[-1]
            res.setdefault(rva, []).append(f"{fn}:{line}")
    return res

def resolve_rip(va):
    foff = va_to_off(va)
    if foff < 0 or foff + 8 > len(pe): return ""
    val = struct.unpack_from("<I", pe, foff)[0]
    if (val & 1) == 1:
        tag = val >> 29
        idx = (val & 0x1FFFFFFF) >> 1
        if tag == 5:
            return f'STR "{get_lit(idx)}"'
        elif tag == 3 and 0 <= idx * 36 < methods_sz:
            mu = struct.unpack_from("<7i4H", meta, methods_off + idx * 36)
            if 0 <= mu[2] * 88 < types_sz:
                tu = struct.unpack_from("<22i", meta, types_off + mu[2] * 88)
                return f"MethodDef {get_mstr(tu[0])}.{get_mstr(mu[0])}"
            return f"MethodDef idx={idx} {get_mstr(mu[0])}"
        return f"MetaUsage(tag={tag}, idx={idx})"
    return ""

def dump_fast(name, rva, end_rva):
    sz = end_rva - rva
    print(f"\n================ {name} (0x{rva:08x}..0x{end_rva:08x}, sz={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    umap = get_usym_dict(rva, sz)
    for k in range(0, len(code), 16):
        chunk = code[k : k + 16]
        hex_s = " ".join(f"{b:02x}" for b in chunk)
        print(f"  +0x{k:03x}: {hex_s}")
    print("  --- USYM & Refs ---")
    for i in range(len(code)):
        cur = rva + i
        if cur in umap:
            print(f"  [+0x{i:03x}] {', '.join(umap[cur])}")
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            trva = rva + i + 5 + disp
            if 0x00100000 <= trva <= 0x02600000:
                tumap = get_usym_dict(trva, 16)
                tinfo = ", ".join(tumap.get(trva, [])[:2])
                print(f"  +0x{i:03x}: {'CALL' if code[i]==0xE8 else 'JMP'} 0x{trva:08x} ({tinfo})")
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            tva = image_base + rva + i + 7 + disp
            rinfo = resolve_rip(tva)
            if rinfo:
                print(f"  +0x{i:03x}: RIP [0x{tva-image_base:08x}] -> {rinfo}")

if __name__ == "__main__":
    targets = [
        ("StreamedTable_SetSorting_2_and_4", 0x015efc40, 0x015f0230),
        ("StreamedTable_OnHeaderClicked", 0x015ec910, 0x015ecb70),
        ("StreamedTable_MakeColumnHeader", 0x015eac30, 0x015eb000),
        ("StreamedTable_BindHeader", 0x015e6230, 0x015e6ca0),
        ("StreamedTable_CreateColumn", 0x015e7dc0, 0x015e83b0),
        ("StreamedTable_SetList", 0x015ef610, 0x015ef890),
        ("StreamedTable_OnSortColumn_UpdateSortColumn", 0x015ee250, 0x015ee450),
        ("StreamedTable_UpdatePersisted_UpdateSortColum", 0x015f1290, 0x015f1550),
        ("StreamedListView_UpdateSortingBinding", 0x015ab800, 0x015ab9b0),
    ]

    for name, s, e in targets:
        dump_fast(name, s, e)
