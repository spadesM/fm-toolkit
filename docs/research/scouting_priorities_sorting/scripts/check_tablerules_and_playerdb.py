import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# 1. Inspect Obj 229, 263, 111, 279, 360 full serialized bytes around TableRules / Columns /OrderedColumns
for oi in (229, 263, 111, 279, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    print(f"\n=== Obj {oi} ({name}) len={len(dbytes)} ===")
    # Print hex and ASCII of dbytes from offset 280 to end-64
    for off in range(280, len(dbytes) - 64, 16):
        chunk = dbytes[off : min(off + 16, len(dbytes) - 64)]
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  +0x{off:03x} ({off:3d}): {chunk.hex(' '):<47} |{asc}|")

# 2. Check all fields and methods of StreamedTable and StreamedListView and TableRule
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in ("FM.UI.dll", "SI.Bindable.dll"):
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname in ("StreamedTable", "StreamedListView") or "TableRule" in tname or "Rule" in tname and "Table" in tname:
            f_start = tu[7]
            f_cnt = tu[17] & 0xFFFF
            m_start = tu[8] # wait: let's check both tu[8] and tu[9]
            print(f"\n=== {iname} :: {tname} (tu={tu[:18]}) ===")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                print(f"  Field {fi - f_start}: {get_mstr(fu[0])}")
