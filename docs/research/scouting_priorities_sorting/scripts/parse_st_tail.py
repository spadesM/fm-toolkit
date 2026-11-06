import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes

# Let's inspect the exact types of Field[0..55] of StreamedTable.UxmlSerializedData from StreamedTable.UxmlSerializedData.Deserialize:
# From Deserialize (0x015f36b0):
# Field[0] InitFunction ([rsi+0x150]): AssetReference (3 strings: GUID, SubObjName, SubObjType)
# Field[1] DragEvents ([rsi+0x158]): List<Event>? Or what?
# Wait! Let's check the exact field types of Type[5957] in metadata!
from check_deep_sorting import meta, hdr, fields_off, types_off, get_mstr

# Let's check how StreamedTable.UxmlSerializedData fields are serialized in dbytes by parsing from the end or beginning!
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    # Find "f45d19f7c2614ae4782f06ccd001fbb1" or "68de34d4e9a0da04c8015b818de5bdf8"
    idx = dbytes.find(b"f45d19f7c2614ae4782f06ccd001fbb1")
    if idx == -1:
        idx = dbytes.find(b"68de34d4e9a0da04c8015b818de5bdf8")
    pos = idx - 4
    print(f"\n=== Obj {oi} ({name}) from ContextMenuData (+0x{pos:03x}, remaining={len(dbytes)-pos} bytes) ===")
    rem = dbytes[pos:]
    for off in range(0, len(rem), 16):
        chunk = rem[off:off+16]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        asciis = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  +0x{pos+off:03x} (rem+0x{off:03x}): {hexs:<48} | {asciis}")
