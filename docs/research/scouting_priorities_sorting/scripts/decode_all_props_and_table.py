import struct, sys, re, json
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\decode_all_props_and_table.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
lit_cnt = str_lit_sz // 8
literals = [
    meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length].decode("utf-8", errors="replace")
    for length, data_idx in (struct.unpack_from("<II", meta, str_lit_off + i * 8) for i in range(lit_cnt))
]

def resolve_string_literal_va(va: int) -> str:
    foff = va_to_off(va)
    if foff < 0:
        return ""
    val = struct.unpack_from("<I", pe, foff)[0]
    if (val >> 29) == 5 and (val & 1) == 1:
        lit_idx = (val & 0x1FFFFFFF) >> 1
        if 0 <= lit_idx < len(literals):
            return literals[lit_idx]
    return ""

# 1. Extract ALL property ID -> string name from PropertyRegistration.Initialise across all assemblies
prop_map = {}
ctx_map = {}

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
        if tname in ("PropertyRegistration", "ContextRegistration"):
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                if get_mstr(mu[0]) == "Initialise":
                    rid = (mu[6] & 0xFFFFFF) - 1
                    if not (0 <= rid < m_cnt_mod):
                        continue
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                    if va == 0:
                        continue
                    rva = va - image_base
                    end_rva = rva_to_end.get(rva, rva + 256)
                    foff = va_to_off(va)
                    code = pe[foff : foff + (end_rva - rva)]
                    print(f"Found {iname}::{tname}.Initialise @ RVA {hex(rva)}..{hex(end_rva)} (size={len(code)})")
                    # Pattern A: 4c 8b 05 <disp32> b9 <u32>
                    for m in re.finditer(rb"\x4c\x8b\x05(....)\xb9(....)", code, re.DOTALL):
                        r8_va = va + m.start() + 7 + struct.unpack("<i", m.group(1))[0]
                        u32 = struct.unpack("<I", m.group(2))[0]
                        s = resolve_string_literal_va(r8_va)
                        if s:
                            if tname == "PropertyRegistration":
                                prop_map[u32] = s
                            else:
                                ctx_map[u32] = s
                    # Pattern B: 33 d2 b9 <u32> e8 .... ... 4c 8b 05 <disp32>
                    for m in re.finditer(rb"\x33\xd2\xb9(....)\xe8....", code, re.DOTALL):
                        pos = m.start()
                        u32 = struct.unpack("<I", m.group(1))[0]
                        window = code[pos : pos + 130]
                        m_r8 = re.search(rb"\x4c\x8b\x05(....)", window, re.DOTALL)
                        if m_r8:
                            r8_va = va + pos + m_r8.end() + struct.unpack("<i", m_r8.group(1))[0]
                            s = resolve_string_literal_va(r8_va)
                            if s:
                                if tname == "PropertyRegistration":
                                    prop_map[u32] = s
                                else:
                                    ctx_map[u32] = s

print(f"Total decoded properties: {len(prop_map)}, contexts: {len(ctx_map)}")

# Map entity IDs to Reference class names
entity_id_to_class = {}
ref_types = {}
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
        if not tname.endswith("Reference"):
            continue
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        methods_dict = {}
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            if 0 <= rid < m_cnt_mod:
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                if va > 0:
                    methods_dict.setdefault(mname, []).append(va - image_base)
                    if mname in ("get_ID", "get_Identifier"):
                        foff = va_to_off(va)
                        if pe[foff] == 0xB8:
                            eid = struct.unpack_from("<I", pe, foff + 1)[0]
                            entity_id_to_class[eid] = tname
        ref_types[tname] = (ti, methods_dict)

def inspect_reference_class(tname):
    if tname not in ref_types:
        print(f"Reference class {tname} not found!")
        return
    ti, mdict = ref_types[tname]
    print(f"\n================ {tname} (Type {ti}) ================")
    for mname, rvas in mdict.items():
        print(f"  Method {mname}: {[hex(r) for r in rvas]}")
    # Decode get_ID
    for id_m in ("get_ID", "get_Identifier"):
        if id_m in mdict:
            rva = mdict[id_m][0]
            foff = va_to_off(image_base + rva)
            if pe[foff] == 0xB8:
                eid = struct.unpack_from("<I", pe, foff + 1)[0]
                print(f"  Entity ID: {hex(eid)} ({struct.pack('<I', eid)})")
    # Decode DerivesFromInternal
    if "DerivesFromInternal" in mdict:
        rva = mdict["DerivesFromInternal"][0]
        end_rva = rva_to_end.get(rva, rva + 128)
        code = pe[va_to_off(image_base + rva) : va_to_off(image_base + end_rva)]
        derives = []
        for m in re.finditer(rb"\x81\xf9(....)", code, re.DOTALL):
            du32 = struct.unpack("<I", m.group(1))[0]
            derives.append(f"{entity_id_to_class.get(du32, hex(du32))} ({hex(du32)})")
        print(f"  DerivesFromInternal: {derives}")
    # Decode GetPropertiesInternal
    if "GetPropertiesInternal" in mdict:
        rva = mdict["GetPropertiesInternal"][0]
        end_rva = rva_to_end.get(rva, rva + 512)
        code = pe[va_to_off(image_base + rva) : va_to_off(image_base + end_rva)]
        props = []
        for m in re.finditer(rb"\xb9(....)\xe8", code, re.DOTALL):
            pu32 = struct.unpack("<I", m.group(1))[0]
            if pu32 in prop_map or all(32 <= b < 127 for b in struct.pack("<I", pu32)):
                props.append((hex(pu32), struct.pack("<I", pu32).decode("ascii", "replace"), prop_map.get(pu32, "???")))
        print(f"  GetPropertiesInternal ({len(props)} props):")
        for p_hex, p_cc, p_name in props:
            print(f"    {p_hex} ('{p_cc}') -> {p_name}")
    # Decode GetPropertyTypeInternal
    if "GetPropertyTypeInternal" in mdict:
        rva = mdict["GetPropertyTypeInternal"][0]
        end_rva = rva_to_end.get(rva, rva + 512)
        dump_func_details(f"{tname}.GetPropertyTypeInternal", rva, end_rva - rva)
        code = pe[va_to_off(image_base + rva) : va_to_off(image_base + end_rva)]
        # Also print any 4-byte constants in code that match prop_map or entity_id_to_class
        for i in range(len(code) - 4):
            u32 = struct.unpack_from("<I", code, i)[0]
            if u32 in prop_map:
                print(f"    @ +0x{i:03x}: PROP {hex(u32)} -> {prop_map[u32]}")
            if u32 in entity_id_to_class:
                print(f"    @ +0x{i:03x}: ENTITY {hex(u32)} -> {entity_id_to_class[u32]}")

for target_cls in [
    "ScoutPlayerPrioritiesReference",
    "ScoutTeamPrioritiesReference",
    "SpecificallyScoutedPersonReference",
    "SpecificallyScoutedTeamReference",
    "PersonSearchReference",
    "TransferActivityPersonReference",
    "RecruitmentRecommendationPersonReference",
    "IPlayerReference",
    "PersonReference",
]:
    inspect_reference_class(target_cls)

# Also dump SpecificallyScoutedPersonReference.GetInstance and .ctor and AcceptsPropertyInternal!
if "SpecificallyScoutedPersonReference" in ref_types:
    _, mdict = ref_types["SpecificallyScoutedPersonReference"]
    for mname, rvas in mdict.items():
        for rva in rvas:
            sz = rva_to_end.get(rva, rva + 128) - rva
            dump_func_details(f"SpecificallyScoutedPersonReference.{mname}", rva, sz)

out_file.close()
