import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import meta, types_off, types_sz, fields_off, get_mstr

for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if tname == "UxmlSerializedData":
        decl_ti = tu[3] # declaringTypeIndex or similar
        # Let's check all fields of tu to find declaring type
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        if f_cnt > 20:
            f0 = get_mstr(struct.unpack_from("<3i", meta, fields_off + f_start * 12)[0])
            f1 = get_mstr(struct.unpack_from("<3i", meta, fields_off + (f_start + 1) * 12)[0])
            print(f"Type[{ti}] fields={f_cnt} f0={f0} f1={f1} tu[:8]={tu[:8]}")
