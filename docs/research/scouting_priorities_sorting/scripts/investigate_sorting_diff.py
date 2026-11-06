import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated

types_cnt = types_sz // 88
il2cpp_types_cnt = 57145
il2cpp_types_va = 0x1829ffc10

def describe_il2cpp_type(type_idx: int) -> str:
    if not (0 <= type_idx < il2cpp_types_cnt):
        return f"type_idx={type_idx}"
    ptr_off = va_to_off(il2cpp_types_va + type_idx * 8)
    type_va = struct.unpack_from("<Q", pe, ptr_off)[0]
    toff = va_to_off(type_va)
    if toff < 0:
        return f"type_idx={type_idx} (bad va)"
    data_val, attrs, t_enum = struct.unpack_from("<QHB", pe, toff)
    if t_enum in (0x11, 0x12) and 0 <= data_val < types_cnt:
        tu = struct.unpack_from("<22i", meta, types_off + data_val * 88)
        return f"{get_mstr(tu[1])}.{get_mstr(tu[0])} (t_enum=0x{t_enum:x}, td={data_val})"
    elif t_enum == 0x15: # GENERICINST
        gclass_off = va_to_off(data_val)
        if gclass_off >= 0:
            g_td = struct.unpack_from("<q", pe, gclass_off)[0]
            if 0 <= g_td < types_cnt:
                tu = struct.unpack_from("<22i", meta, types_off + g_td * 88)
                return f"GenericInst {get_mstr(tu[1])}.{get_mstr(tu[0])} (t_enum=0x15, td={g_td})"
    elif t_enum in (0x1d, 0x14): # SZARRAY / ARRAY
        elem_off = va_to_off(data_val)
        return f"Array(t_enum=0x{t_enum:x}, data=0x{data_val:x})"
    return f"Il2CppType(idx={type_idx}, data=0x{data_val:x}, t_enum=0x{t_enum:x})"

print("=== Resolved Il2CppType Indices ===")
for tidx in [32982, 56117, 29016, 12128, 23676, 23672, 38755, 37208, 53626, 34369, 34769, 47725, 47713, 47723, 56486, 56484, 38760]:
    print(f"  Type[{tidx}] -> {describe_il2cpp_type(tidx)}")

print("\n=== Disassembling Bindings.GetNthProperty, Bindings.Bind, Bindings.Unbind ===")
for name, rva in [
    ("Bindings.GetNthProperty", 0x014c1450),
    ("Bindings.Unbind", 0x014c6110),
    ("Bindings.Bind", 0x014bce90),
    ("StreamedListView.GetSorter", 0x015a5bb0),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)

print("\n=== Searching types related to ScoutPriorities or SpecificallyScouted ===")
for ti in range(types_cnt):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if any(k in tname.lower() or k in tns.lower() for k in ("scoutpriorit", "specificallyscouted", "shortlist")):
        m_start = tu[7]
        m_count = tu[17]
        print(f"Type[{ti}] {tns}.{tname} (methods={m_count})")
        for mi in range(m_start, m_start + m_count):
            mu = struct.unpack_from("<7i2H", meta, methods_off + mi * 32)
            mname = get_mstr(mu[0])
            mrva = rva_to_method_name.get(mu[0], "")
            # Wait, find RVA from rva_to_method_name by matching full name or let's print method name
            print(f"    Method[{mi}] {mname} (token=0x{mu[6]:x})")
