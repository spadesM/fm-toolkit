import struct, sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf

# Let's build a fast RVA -> MethodDef name lookup from global-metadata.dat or il2cpp.usym
# In il2cpp.usym, each record has (rva, parent_idx, sym_off, file_off, line, flags)
# When file_off == 0, sym_off is the symbol name!
def get_sym_name(target_rva):
    lo, hi = 0, dhf.sym_count - 1
    while lo < hi:
        mid = (lo + hi) // 2
        rva = struct.unpack_from("<I", dhf.udata, dhf.records_off + mid * 24)[0]
        if rva <= target_rva: lo = mid + 1
        else: hi = mid
    for idx in range(max(0, lo - 15), min(dhf.sym_count, lo + 5)):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", dhf.udata, dhf.records_off + idx * 24)
        if rva <= target_rva and sym_off != 0 and file_off == 0:
            s = dhf.get_ustr(sym_off)
            if target_rva - rva < 0x1000:
                return f"{s}+0x{target_rva-rva:x}"
    return ""

for name, s, e in [
    ("ApplySorting (0x015a4260..0x015a4700)", 0x015a4260, 0x015a4700),
    ("SubscribeSortPath (0x015a4850..0x015a49b0)", 0x015a4850, 0x015a49b0),
    ("OnSortValueChanged (0x015a7ff0..0x015a8110)", 0x015a7ff0, 0x015a8110),
    ("CheckSortComplete (0x015a8610..0x015a86d0)", 0x015a8610, 0x015a86d0),
    ("ProcessSortValue (0x015a8cb0..0x015a8eb0)", 0x015a8cb0, 0x015a8eb0),
    ("EvaluateItemSort (0x015aa320..0x015aa640)", 0x015aa320, 0x015aa640),
]:
    print(f"\n=== {name} ===")
    off = dhf.va_to_off(dhf.image_base + s)
    code = dhf.pe[off : off + (e - s)]
    umap = dhf.get_usym_dict(s, e - s)
    for i in range(len(code)):
        cur = s + i
        if cur in umap:
            print(f"  [+0x{i:03x}] (0x{cur:08x}) {', '.join(umap[cur])}")
        if i + 5 <= len(code) and code[i] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", code, i + 1)[0]
            trva = cur + 5 + disp
            if 0x00100000 <= trva <= 0x02600000:
                sname = get_sym_name(trva)
                tumap = dhf.get_usym_dict(trva, 16)
                tinfo = ", ".join(tumap.get(trva, [])[:2])
                print(f"  +0x{i:03x}: {'CALL' if code[i]==0xE8 else 'JMP'} 0x{trva:08x} [{sname}] ({tinfo})")
        if i + 7 <= len(code) and code[i] in (0x48, 0x4C) and code[i+1] in (0x8B, 0x8D) and (code[i+2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            tva = dhf.image_base + cur + 7 + disp
            rinfo = dhf.resolve_rip(tva)
            if rinfo:
                print(f"  +0x{i:03x}: RIP -> {rinfo}")
