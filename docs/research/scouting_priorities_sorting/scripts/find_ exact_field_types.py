import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, off_to_va, image_base,
    types_off, types_sz, fields_off, fields_sz, get_mstr
)
from parse_st_data_exact import get_ref_bytes

# Let's check what Deserialize (0x015f36b0) does when reading SelectionLimitBinding (val_off=0x1a0) and FooterBinding (val_off=0x1c0)!
# At +0x105 (flag_off=0x222, Field[10] SelectionLimitBinding):
#   48 8b 86 a0 01 00 00 -> mov rax, [rsi+0x1a0]
#   48 8d 8f 48 09 00 00 -> lea rcx, [rdi+0x948]
#   48 89 87 48 09 00 00 -> mov [rdi+0x948], rax
# Wait: it's an 8-byte pointer in memory! What class is type_idx=23620?
# Let's find all classes in SI.Bindable.dll with 1, 2, 3, 4, 5 fields!
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if "Binding" in tname or "AssetReference" in tname or "VisualFunction" in tname:
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        byval = tu[5]
        print(f"TypeDef[{ti}] byval={byval} {tns}.{tname} (fields={f_cnt}, parent={tu[2]})")
        for i in range(f_cnt):
            fu = struct.unpack_from("<3i", meta, fields_off + (f_start + i) * 12)
            print(f"  Field[{i}]: {get_mstr(fu[0])} (type_idx={fu[1]})")
