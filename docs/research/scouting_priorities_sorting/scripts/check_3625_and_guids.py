import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import dump_fast, root

# 1. Dump StreamedTable around 0x015ee000..0x015ee450 and 0x015f0040..0x015f0580
dump_fast("StreamedTable_015ee000_015ee450", 0x015ee000, 0x015ee450)
dump_fast("StreamedTable_TrySetColumnsAndSort_015f0040", 0x015f0040, 0x015f0580)

# 2. Dump StreamedTable.UxmlSerializedData.Deserialize around +0x040..+0x200 to see how m_initFunction (+0x940) is used!
# Let's search for 0x940 (40 09 00 00) and 0x910 (10 09 00 00) in StreamedTable (0x015de000..0x015f6000)
from dump_headers_fast import pe, image_base, va_to_off, get_usym_dict
s_off = va_to_off(image_base + 0x015de000)
e_off = va_to_off(image_base + 0x015f6000)
chunk = pe[s_off:e_off]
for field_off, fname in [(b"\x40\x09\x00\x00", "+0x940 (m_initFunction)"), (b"\x10\x09\x00\x00", "+0x910 (m_initialisationHandler)"), (b"\xd8\x07\x00\x00", "+0x7d8 (DisableSorting)"), (b"\x38\x08\x00\x00", "+0x838 (m_streamedTableView)")]:
    print(f"\n=== References to {fname} in StreamedTable ===")
    pos = 0
    while True:
        idx = chunk.find(field_off, pos)
        if idx == -1:
            break
        rva = 0x015de000 + idx
        umap = get_usym_dict(rva - 16, 32)
        uinfo = []
        for k in sorted(umap):
            uinfo.extend(umap[k])
        print(f"  RVA 0x{rva:08x}: bytes={chunk[idx-4:idx+8].hex(' ')} | USYM={uinfo[:3]}")
        pos = idx + 1
