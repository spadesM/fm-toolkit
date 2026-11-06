import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")

from check_sorting_details import dump_fast
from parse_st_data_exact import get_ref_bytes

# 1. Dump StreamedListView.UxmlSerializedData.Deserialize (0x015b0b50)
dump_fast("StreamedListView.UxmlSerializedData.Deserialize", 0x015b0b50, 0x015b1300)

# 2. Let's inspect all bytes of Obj 229, 263, 111, 297, 360 from +0x100 to end
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    print(f"\n================ {oi}: {name} (len=0x{len(dbytes):x}) ================")
    for off in range(0, len(dbytes), 16):
        chunk = dbytes[off:off+16]
        ascii_s = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  +0x{off:03x} (end-0x{len(dbytes)-off:03x}): {chunk.hex(' '):<47} | {ascii_s}")
