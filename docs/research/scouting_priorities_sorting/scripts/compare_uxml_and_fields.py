import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

from check_deep_sorting import (
    pe, meta, hdr, image_base, va_to_off, off_to_va, get_mstr,
    types_off, types_sz, fields_off, fields_sz, methods_off, methods_sz,
    images_off, images_sz, modules
)
from parse_st_data_exact import get_ref_bytes
from disasm_sorting_callbacks import resolve_meta_usage

# 1. Print fields & methods of StreamedTable, StreamedTable.UxmlSerializedData, StreamedListView, SpecificallyScoutedPersonReference
num_types = types_sz // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if ti in (5967, 5968, 909) or tname in ("StreamedTable", "StreamedListView", "VirtualisedList", "SpecificallyScoutedPersonReference") or "ScoutPriorit" in tname:
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\n=== Type[{ti}] {tns}.{tname} (fields={f_cnt}, methods={m_cnt}, parent_byval={tu[3]}) ===")
        for fi in range(f_start, f_start + f_cnt):
            fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
            fname = get_mstr(fu[0])
            print(f"  Field[{fi - f_start:2d}] (global {fi}): {fname} (type_byval={fu[1]})")
        if ti == 909 or "ScoutPriorit" in tname:
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                print(f"  Method[{mi - m_start:2d}]: {mname}")

# 2. Compare StreamedTable/UxmlSerializedData bytes for Obj 229, 263, 111, 297, 360
print("\n=== Comparing StreamedTable/UxmlSerializedData across Obj 229, 263, 111, 297, 360 ===")
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    print(f"\n--- Obj {oi} ({name}) rid={rid} len={len(dbytes)} (0x{len(dbytes):x}) ---")
    p = 0
    while p + 4 <= len(dbytes):
        val_u32 = struct.unpack_from("<I", dbytes, p)[0]
        if 1 <= val_u32 <= 200 and p + 4 + val_u32 <= len(dbytes):
            s = dbytes[p + 4 : p + 4 + val_u32]
            pad = (4 - (val_u32 % 4)) % 4
            if p + 4 + val_u32 + pad <= len(dbytes) and dbytes[p + 4 + val_u32 : p + 4 + val_u32 + pad] == b"\x00" * pad:
                if all(32 <= b < 127 for b in s):
                    print(f"  +0x{p:03x} (end-0x{len(dbytes)-p:03x}): STR ({val_u32}) {s.decode('ascii')!r}")
                    p += 4 + val_u32 + pad
                    continue
        if val_u32 != 0:
            print(f"  +0x{p:03x} (end-0x{len(dbytes)-p:03x}): 0x{val_u32:08x} ({val_u32})")
        p += 4
