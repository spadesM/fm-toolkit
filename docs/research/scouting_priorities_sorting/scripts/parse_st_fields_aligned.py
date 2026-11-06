import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# Let's check all methods of VirtualisedList in SI.Bindable.dll and see where +0x5c1 (m_Reorderable) or sorting is used!
# Also let's check StreamedTable.UxmlSerializedData fields in Obj 229, 263, 111, 297, 360 after Binding (+0x110)!
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    print(f"\n=== Obj {oi} ({name}) total_len={len(dbytes)} (0x{len(dbytes):x}) ===")
    # Print the last 0x100 bytes where bools and flags of StreamedTable.UxmlSerializedData live!
    start = max(0, len(dbytes) - 0x120)
    for off in range(start, len(dbytes), 16):
        chunk = dbytes[off:off+16]
        print(f"  +0x{off:03x} (end-0x{len(dbytes)-off:03x}): {chunk.hex(' ')}")
