import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import (
    dump_fast, pe, meta, hdr, str_lit_off, str_lit_sz, str_lit_data_off, str_lit_data_sz,
    str_off, str_sz, methods_off, methods_sz, types_off, types_sz, get_mstr, get_lit,
    image_base, sections, va_to_off, resolve_rip, get_usym_dict
)

# 1. Dump key methods with USYM & RIP annotations
targets = [
    ("Bindings.GetNthProperty", 0x014c1450, 0x014c1670),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x015a8cb0),
    ("StreamedListView.SortRows_and_UpdateEnabled", 0x015aab80, 0x015ab000),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0, 0x015e5c00),
    ("StreamedTable.InitialiseColumns", 0x015ea870, 0x015eac30),
]
for name, s, e in targets:
    dump_fast(name, s, e)

# 2. Check all TypeDefinitions in global-metadata.dat for type indices 32982 and 38755 (or nearby)
num_types = types_sz // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    # tu[5] is byvalTypeIndex
    if abs(tu[5] - 32982) <= 5 or abs(tu[5] - 38755) <= 5:
        print(f"TypeDef[{ti}] {get_mstr(tu[1])}.{get_mstr(tu[0])}: byval={tu[5]}, parent={tu[3]}, decl={tu[2]}")
