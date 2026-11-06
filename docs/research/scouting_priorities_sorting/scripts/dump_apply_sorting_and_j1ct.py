import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, sections, dump_func_details, get_mstr, rva_to_end, rva_to_method_name

str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]

def get_str_literal(idx: int) -> str:
    if idx < 0 or idx * 8 >= str_lit_sz:
        return f"<oob:{idx}>"
    length, data_idx = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    raw = meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length]
    return raw.decode("utf-8", errors="replace")

def resolve_data_rva(rva: int) -> str:
    off = va_to_off(image_base + rva)
    if off < 0 or off + 8 > len(pe):
        return ""
    val = struct.unpack_from("<Q", pe, off)[0]
    if (val >> 29) == 5:
        idx = (val & 0x1FFFFFFF) >> 1
        return f"str_lit[{idx}] = {get_str_literal(idx)!r}"
    elif (val >> 29) in (1, 2, 3, 4, 6):
        return f"meta_usage(tag={val>>29}, idx={(val & 0x1FFFFFFF)>>1})"
    return ""

def dump_with_strings(label, rva, sz=None):
    if sz is None:
        sz = rva_to_end.get(rva, rva + 256) - rva
    dump_func_details(label, rva, sz)
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    print("  --- RIP Data Annotations ---")
    for i in range(len(code) - 7):
        if code[i] in (0x48, 0x4c) and code[i+1] in (0x8b, 0x8d) and (code[i+2] & 0xc7) == 0x05:
            disp = struct.unpack_from("<i", code, i + 3)[0]
            trva = rva + i + 7 + disp
            info = resolve_data_rva(trva)
            if info:
                print(f"  +0x{i:03x}: RIP -> 0x{trva:08x} ({info})")

# 1. Decode J1Ct (0x7443314a) and ao3d (0x64336f61 / 0x616f3364) in PropertyRegistration.Initialise!
# Let's search PropertyRegistration.Initialise (0x003e4f30..0x004c5d06) for 0x7443314a (4a 31 43 74)
init_off = va_to_off(image_base + 0x003e4f30)
init_sz = 0x004c5d06 - 0x003e4f30
init_code = pe[init_off : init_off + init_sz]
pos = 0
print("=== Searching for J1Ct (0x7443314a) in PropertyRegistration.Initialise ===")
while True:
    idx = init_code.find(b"\x4a\x31\x43\x74", pos)
    if idx == -1:
        break
    rva = 0x003e4f30 + idx
    print(f"Found J1Ct at RVA 0x{rva:08x}")
    dump_with_strings(f"J1Ct_reg_0x{rva:08x}", rva - 0x40, 0x280)
    pos = idx + 1

# 2. Dump Header and StreamedTable click handlers + StreamedListView sorting methods
dump_with_strings("Header.SetupClickHandler", 0x015df7e0)
dump_with_strings("Header.<>c__DisplayClass36_0.<.ctor>b__0", 0x015f2ea0)
dump_with_strings("StreamedTable_closure_area", 0x015f2ec0, 0x200)
dump_with_strings("StreamedListView.HasSorting", 0x015a5f20)
dump_with_strings("StreamedListView.ApplySorting", 0x015a4260)
dump_with_strings("StreamedListView.EndStateChange", 0x015a5350)
dump_with_strings("StreamedListView.ResolveStateChanges", 0x015a9620)
dump_with_strings("StreamedListView.RefreshInternal", 0x015a9060)
