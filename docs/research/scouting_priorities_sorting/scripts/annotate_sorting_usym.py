import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
from check_deep_sorting import pe, meta, image_base, va_to_off, rva_to_end, rva_to_method_name, get_mstr, methods_off, types_off

root = resolve_fm_install_dir()
hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
lit_cnt = str_lit_sz // 8
literals = [
    meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length].decode("utf-8", errors="replace")
    for length, data_idx in (struct.unpack_from("<II", meta, str_lit_off + i * 8) for i in range(lit_cnt))
]

# Load il2cpp.usym
usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
if not usym_path.exists():
    usym_path = root / "il2cpp.usym"
usym_map = {}
if usym_path.exists():
    udata = usym_path.read_bytes()
    _, _, sym_count, _, _, _ = struct.unpack_from("<4sIIIII", udata, 0)
    records_off = 24
    str_table_off = records_off + sym_count * 24
    str_blob = udata[str_table_off:]
    def get_ustr(off):
        if off <= 0 or off >= len(str_blob):
            return ""
        end = str_blob.find(b"\x00", off)
        return str_blob[off:end].decode("utf-8", errors="replace")
    # Filter RVAs in [0x014b0000, 0x01630000]
    for i in range(sym_count):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + i * 24)
        if 0x014b0000 <= rva <= 0x01630000:
            usym_map.setdefault(rva, []).append((get_ustr(sym_off), get_ustr(file_off), line))

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
        elif tag == 3:
            if 0 <= idx * 36 < hdr[13]:
                mu = struct.unpack_from("<7i4H", meta, methods_off + idx * 36)
                if 0 <= mu[2] * 88 < hdr[41]:
                    tu = struct.unpack_from("<22i", meta, types_off + mu[2] * 88)
                    return f"MethodDef {get_mstr(tu[0])}.{get_mstr(mu[0])}"
            return f"MetaUsage(tag=3, idx={idx})"
        elif tag in (1, 2, 4, 6):
            return f"MetaUsage(tag={tag}, idx={idx})"
    return ""

def dump_annotated(label, rva, sz=None):
    if sz is None:
        sz = rva_to_end.get(rva, rva + 256) - rva
    print(f"\n================ {label} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for i in range(len(code)):
        cur_rva = rva + i
        if cur_rva in usym_map:
            for sym, fn, ln in usym_map[cur_rva]:
                short_fn = fn.split("/")[-1].split("\\")[-1] if fn else ""
                if ln > 0 or sym:
                    print(f"  [USYM +0x{i:03x}] {short_fn}:{ln} ({sym})")
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            target_rva = rva + i + 5 + disp
            names = rva_to_method_name.get(target_rva, [])
            if names or (0x00500000 <= target_rva <= 0x02500000):
                op = "CALL" if code[i] == 0xE8 else "JMP"
                print(f"  +0x{i:03x}: {op} 0x{target_rva:08x} -> {', '.join(names[:4])}")
        # Check RIP-relative mov/lea: [48/4c] [8b/8d] [modrm with mod=00, rm=101 -> (b & 0xC7) == 0x05]
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            target_va = image_base + rva + i + 7 + disp
            info = resolve_rip_va(target_va)
            if info:
                print(f"  +0x{i:03x}: RIP [0x{target_va - image_base:08x}] -> {info}")

if __name__ == "__main__":
    dump_annotated("StreamedListView.ApplySorting", 0x015a4260)
    dump_annotated("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320)
    dump_annotated("StreamedListView.BindSortPathNextDepth", 0x015a4850)
    dump_annotated("StreamedListView.OnSortingDataChanged", 0x015a7ff0)
    dump_annotated("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0)
    dump_annotated("StreamedTable.OnHeaderClicked", 0x015ec910)
    dump_annotated("StreamedTable.SetSorting", 0x015efce0)
