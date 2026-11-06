import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)

num_typedefs = dhf.types_sz // 88
pat = struct.pack("<q", num_typedefs)
pos = 0
while True:
    idx = pe.find(pat, pos)
    if idx == -1:
        break
    if struct.unpack_from("<q", pe, idx + 16)[0] == num_typedefs:
        mr_off = idx - 80
        mr = struct.unpack_from("<16Q", pe, mr_off)
        break
    pos = idx + 1

types_cnt, types_va = mr[6], mr[7]
mspecs_cnt, mspecs_va = mr[8], mr[9]
ginsts_cnt, ginsts_va = mr[2], mr[3]
types_table_off = va_to_off(types_va)
mspecs_table_off = va_to_off(mspecs_va)
ginsts_table_off = va_to_off(ginsts_va)

def format_il2cpp_type_va(t_va):
    t_off = va_to_off(t_va)
    if t_off < 0:
        return f"TypeVA(0x{t_va:x})"
    data_val, attrs = struct.unpack_from("<QI", pe, t_off)
    t_enum = (attrs >> 16) & 0xFF
    if t_enum in (0x12, 0x11, 0x1c, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e):
        if 0 <= data_val < num_typedefs:
            tu = struct.unpack_from("<22i", meta, types_off + data_val * 88)
            ns = get_mstr(tu[1])
            nm = get_mstr(tu[0])
            return f"{ns}.{nm}" if ns else nm
    elif t_enum == 0x15:
        gclass_off = va_to_off(data_val)
        tdef_idx_or_va, ginst_va = struct.unpack_from("<QQ", pe, gclass_off)
        if tdef_idx_or_va > image_base:
            gt_off = va_to_off(tdef_idx_or_va)
            td_idx = struct.unpack_from("<Q", pe, gt_off)[0]
        else:
            td_idx = tdef_idx_or_va
        base_name = get_mstr(struct.unpack_from("<22i", meta, types_off + td_idx * 88)[0]) if 0 <= td_idx < num_typedefs else f"TD({td_idx})"
        gi_off = va_to_off(ginst_va)
        argc, argv_va = struct.unpack_from("<QQ", pe, gi_off)
        argv_off = va_to_off(argv_va)
        args = []
        for ai in range(min(argc, 8)):
            arg_tva = struct.unpack_from("<Q", pe, argv_off + ai * 8)[0]
            args.append(format_il2cpp_type_va(arg_tva))
        return f"{base_name}<{', '.join(args)}>"
    elif t_enum == 0x1d:
        return f"{format_il2cpp_type_va(data_val)}[]"
    return f"Type(enum=0x{t_enum:02x}, data=0x{data_val:x})"

def format_il2cpp_type(type_idx):
    if not (0 <= type_idx < types_cnt):
        return f"TypeIdx({type_idx})"
    t_va = struct.unpack_from("<Q", pe, types_table_off + type_idx * 8)[0]
    return format_il2cpp_type_va(t_va)

def format_method_spec(ms_idx):
    if not (0 <= ms_idx < mspecs_cnt):
        return f"MethodSpec({ms_idx})"
    mdef_idx, cinst_idx, minst_idx = struct.unpack_from("<iii", pe, mspecs_table_off + ms_idx * 12)
    if 0 <= mdef_idx * 36 < dhf.methods_sz:
        mu = struct.unpack_from("<7i4H", meta, methods_off + mdef_idx * 36)
        tname = get_mstr(struct.unpack_from("<22i", meta, types_off + mu[2] * 88)[0]) if 0 <= mu[2] < num_typedefs else f"T({mu[2]})"
        s = f"{tname}.{get_mstr(mu[0])}"
    else:
        s = f"MDef({mdef_idx})"
    for label, gidx in (("C", cinst_idx), ("M", minst_idx)):
        if 0 <= gidx < ginsts_cnt:
            gi_va = struct.unpack_from("<Q", pe, ginsts_table_off + gidx * 8)[0]
            gi_off = va_to_off(gi_va)
            argc, argv_va = struct.unpack_from("<QQ", pe, gi_off)
            argv_off = va_to_off(argv_va)
            args = []
            for ai in range(min(argc, 8)):
                arg_tva = struct.unpack_from("<Q", pe, argv_off + ai * 8)[0]
                args.append(format_il2cpp_type_va(arg_tva))
            s += f"[{label}:<{', '.join(args)}>]"
    return s

rip_rvas = [
    ("ApplySorting +0x068", 0x02e10d28),
    ("SetupRow +0x27e", 0x02e24428),
    ("SetupRow +0x2a1", 0x02e37848),
    ("SetupRow +0x2c9", 0x02e07f68),
    ("ProcessSortingDataChanged +0x0da", 0x02e1c298),
    ("ProcessSortingDataChanged +0x154", 0x02e06ea8),
    ("SortData.HasReceived +0x00b", 0x02e207c8),
    ("SortComparer.Compare_2 +0x069", 0x02e3b870),
    ("SortComparer.Compare_2 +0x09f", 0x02e3b878),
    ("SortComparer.Compare_2 +0x18b", 0x02df8a38),
    ("SortComparer.Compare_2 +0x1e8", 0x02e06ea8),
    ("SortComparer.Compare_2 +0x204", 0x02e06ea8),
    ("OnSortBindingChanged +0x0c4", 0x02e0a170),
    ("OnSortBindingChanged +0x119", 0x02e108e0),
    ("OnSortBindingChanged +0x166", 0x02de28b0),
    ("OnSortBindingChanged +0x1c5", 0x02e10d28),
    ("OnSortBindingChanged +0x20f", 0x02e0a688),
    ("OnSortBindingChanged +0x23a", 0x02e255a0),
    ("OnSortBindingChanged +0x296", 0x02e254d0),
    ("OnSortingDataChanged +0x09d", 0x02de6478),
    ("UpdateSortingBinding +0x02f", 0x02ddebb0),
    ("UpdateSortingBinding +0x03b", 0x02e1fb30),
    ("UpdateSortingBinding +0x0bf", 0x02df0610),
    ("UpdateSortingBinding +0x0d8", 0x02e20740),
    ("UpdateSortingBinding +0x0ef", 0x02e20320),
    ("UpdateSortingBinding +0x107", 0x02e08618),
    ("UpdateSortingBinding +0x116", 0x02e1fce8),
    ("UpdateSortingBinding +0x14c", 0x02e056a0),
]
for label, rva in rip_rvas:
    foff = va_to_off(image_base + rva)
    if foff < 0:
        print(f"{label:38s}: [0x{rva:08x}] BSS")
        continue
    val = struct.unpack_from("<I", pe, foff)[0]
    tag = val >> 29
    idx = (val & 0x1FFFFFFF) >> 1
    desc = ""
    if tag in (1, 2):
        desc = format_il2cpp_type(idx)
    elif tag == 6:
        desc = format_method_spec(idx)
    print(f"{label:38s}: [0x{rva:08x}] tag={tag} idx={idx:6d} -> {desc}")
