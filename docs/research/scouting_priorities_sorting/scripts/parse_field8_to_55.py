import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes

# Let's check the size of each type from Field[8] to Field[55] in StreamedTable.UxmlSerializedData:
# Field[ 8]: AddEvents (type_idx=27003 -> List, 4 bytes if empty)
# Field[ 9]: MigrateDragEvent (type_idx=37147 -> string, 4 bytes if empty)
# Field[10]: SelectionLimitBinding (type_idx=23620 -> BindingRemap / BindingPath? Let's check size!)
# Field[11]: MigrateSelectionEvent (type_idx=37147 -> string)
# Field[12]: DefaultSelectFirstElement (type_idx=23780 -> bool, 4 bytes aligned)
# Field[13]: SelectionCellID (type_idx=37147 -> string)
# Field[14]: FooterBinding (type_idx=23620 -> BindingRemap / BindingPath)
# Field[15]: AllowColumnReordering (type_idx=23780 -> bool)
# Field[16]: AllowColumnResizing (type_idx=23780 -> bool)
# Field[17]: ResizeColumnWidthsToFit (type_idx=23780 -> bool)
# Field[18]: ShowFooter (type_idx=23780 -> bool)
# Field[19]: ViewDropdownName (type_idx=37147 -> string)
# Field[20]: DefaultSelectedColumn (type_idx=37147 -> string)
# Field[21]: DragCellID (type_idx=37147 -> string)
# Field[22]: DisableSorting (type_idx=23780 -> bool)
# Field[23]: SortedColumn (type_idx=37147 -> string)
# Field[24]: DisableRowContextMenu (type_idx=23780 -> bool)
# Field[25]: RemoveCellID (type_idx=37147 -> string)
# Field[26]: MigrateAddEvent (type_idx=37147 -> string)
# Field[27]: MigrateRemoveEvent (type_idx=37147 -> string)
# Field[28..55]: 28 UxmlAttributeFlags (each is an enum -> 4 bytes or 1 byte?)

# Let's look at Obj 229 from rem+0x0a0 to rem+0x160 (192 bytes = 48 dwords!):
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    idx = dbytes.find(b"f45d19f7c2614ae4782f06ccd001fbb1")
    if idx != -1:
        pos = idx - 4 + 0x0a0
    else:
        idx = dbytes.find(b"68de34d4e9a0da04c8015b818de5bdf8")
        pos = idx - 4 + 0x038 + 0x018 + 0x018
    tail = dbytes[pos:]
    print(f"\n=== Obj {oi} ({name}) from Field[8] AddEvents (+0x{pos:03x}, len={len(tail)} bytes) ===")
    for off in range(0, len(tail), 4):
        u32 = struct.unpack_from("<I", tail, off)[0]
        raw4 = tail[off:off+4]
        print(f"  +0x{off:02x} (abs +0x{pos+off:03x}): {raw4.hex(' ')} (u32={u32})")
