import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_sorting_details import dump_fast, meta, methods_off, types_off, get_mstr, udata, sym_count, records_off, get_ustr

# Find <MakeColumnHeader>b__0 in usym or around StreamedTable
for idx in range(sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    if 0x015e5000 <= rva <= 0x015f4000:
        if line in (2739, 2740, 2741, 2742):
            print(f"Line {line} at RVA 0x{rva:08x}: sym={get_ustr(sym_off)} file={get_ustr(file_off)}")

targets = [
    ("EntryForColumn_015e9450", 0x015e9450, 0x015e9570),
    ("TryFindSortedColumn_and_TrySetColumnsAndSort", 0x015eff70, 0x015f0230),
    ("SetNoSorting_015ef750", 0x015ef750, 0x015ef890),
    ("OnViewSet_and_RebuildInternal_and_RefreshInternal", 0x015ee7a0, 0x015eef50),
    ("BindToDataInternal_015e6d70", 0x015e6d70, 0x015e7580),
    ("Around_015f2950_DisplayClasses", 0x015f2950, 0x015f3200),
]
for name, s, e in targets:
    dump_fast(name, s, e)
