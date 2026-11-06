import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import (
    pe, meta, types_off, types_sz, methods_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated

# 1. Dump BindSortPathNextDepth, StreamedListView.RefreshInternal, StreamedTable.BindHeader, 0x00abf5a0, 0x00abf660, 0x00a28ae0
for name, rva in [
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("0x00abf5a0 (called in StreamedTable.RefreshInternal on m_headerLookupBySorting)", 0x00abf5a0),
    ("0x00abf660 (called in StreamedTable.RefreshInternal on m_headerLookupByPluginSorting)", 0x00abf660),
    ("0x00a28ae0 (called in RefreshInternal and UpdatePersistedColumnSortingData)", 0x00a28ae0),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)

# 2. Find classes in GameAssembly.dll related to InitialiseStreamedTable / TableViewCollection
num_types = types_sz // 88
for ti in range(num_types):
    toff = types_off + ti * 88
    tu = struct.unpack_from("<22I", meta, toff)
    tname = get_mstr(tu[0])
    if any(k in tname.lower() for k in ("streamedtable", "tableview", "tablefactory", "scoutpriorit")):
        print(f"Type [{ti}] {tname}")
        mstart = tu[9]
        mcount = tu[16] & 0xFFFF
        for mi in range(mstart, mstart + mcount):
            moff = methods_off + mi * 32
            mname_idx = struct.unpack_from("<I", meta, moff)[0]
            mname = get_mstr(mname_idx)
            for rva, names in rva_to_method_name.items():
                if f"{tname}.{mname}" in names:
                    print(f"    0x{rva:08x}: {tname}.{mname}")
