import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name
from check_j1ct_and_nth_prop import get_mstr, get_str_literal, dump_with_strings

# Build Il2CppType table (hdr[36], hdr[37] or hdr[40], hdr[41])
# Let's check what hdr offsets correspond to TypeDefinitions vs Types
types_off, types_sz = hdr[40], hdr[41] # TypeDefinitions (88 bytes each)
byval_to_type = {}
for ti in range(types_sz // 88):
    toff = types_off + ti * 88
    tu = struct.unpack_from("<22i", meta, toff)
    tname = f"{get_mstr(tu[1])}.{get_mstr(tu[0])}".strip(".")
    byval_to_type[tu[5]] = tname
    byval_to_type[ti] = f"td[{ti}]:{tname}"

def resolve_meta_usage(rva: int) -> str:
    off = va_to_off(image_base + rva)
    if off < 0 or off + 8 > len(pe):
        return ""
    val = struct.unpack_from("<Q", pe, off)[0]
    tag = val >> 29
    idx = (val & 0x1FFFFFFF) >> 1
    if tag == 5:
        return f"str_lit[{idx}] = {get_str_literal(idx)!r}"
    elif tag in (1, 2):
        tname = byval_to_type.get(idx, f"type_idx={idx}")
        return f"meta_type(tag={tag}, idx={idx} -> {tname})"
    elif tag in (3, 4, 6):
        return f"meta_usage(tag={tag}, idx={idx})"
    return ""

# Also let's find the exact property registrations of J1Ct's 7 properties:
#From steps/4299/output.txt:
#  plyr (0x706c7972 LE): 0x0046ede5
#  axMd (0x644d7861 LE): 0x0046b097
#  EEYc (0x63594545 LE): 0x0046cb53
#  3cDu (0x75446333 LE): 0x00468d8f
#  vLuq (0x71754c76 LE): 0x00468ca3
#  _Nqs (0x73714e20 LE): 0x00468c2d
#  sWGn (0x6e475773 LE): 0x00468bb7
print("=== 1. Exact Property Names of J1Ct's 7 Properties ===")
for label, rva in [
    ("plyr (0x706c7972)", 0x0046ede5),
    ("axMd (0x644d7861)", 0x0046b097),
    ("EEYc (0x63594545)", 0x0046cb53),
    ("3cDu (0x75446333)", 0x00468d8f),
    ("vLuq (0x71754c76)", 0x00468ca3),
    ("_Nqs (0x73714e20)", 0x00468c2d),
    ("sWGn (0x6e475773)", 0x00468bb7),
]:
    off = va_to_off(image_base + rva)
    chunk = pe[off - 1 : off + 100]
    for i in range(len(chunk) - 7):
        if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
            disp = struct.unpack_from("<i", chunk, i + 3)[0]
            insn_rva = (rva - 1) + i
            trva = insn_rva + 7 + disp
            print(f"  {label:20s} @ 0x{rva:08x} -> {resolve_meta_usage(trva)}")
            break

# 2. Let's inspect all methods of SpecificallyScoutedPersonReference around 0x00696ef0..0x00697700
print("\n=== 2. SpecificallyScoutedPersonReference Methods (0x006971c0..0x00697700) ===")
dump_with_strings("SpecificallyScoutedPersonReference (0x006971c0..0x00697700)", 0x006971c0, 0x540)

# 3. Let's inspect OnSortingDataChanged (0x015a7ff0) and PostSortingDataChanged (0x015a8610)
dump_with_strings("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 0x180)
dump_with_strings("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x180)
