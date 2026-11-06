import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import meta, hdr, fields_off, types_off, get_mstr

# Let's check how type_idx in FieldDef maps to TypeDef!
# In IL2CPP metadata, hdr[28], hdr[29] or similar is Il2CppType table? No, let's find all TypeDefs by name:
for ti in range(hdr[41] // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if any(w in tname for w in ("AssetReference", "BindingRemap", "UxmlAttributeFlags")):
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        if f_cnt > 0:
            print(f"TypeDef[{ti}] {get_mstr(tu[1])}.{tname} (fields={f_cnt}, parent={tu[2]})")
            for i in range(f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + (f_start + i) * 12)
                print(f"  Field[{i}]: {get_mstr(fu[0])}")
