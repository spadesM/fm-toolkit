import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, get_mstr, image_base, va_to_off, rva_to_end,
    images_off, images_sz, types_off, types_sz, methods_off, modules,
    rva_to_method_name, dump_func_details
)

# Find StreamedListView and StreamedTable type indices and any nested types
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if any(k in tname for k in ("StreamedListView", "StreamedTable", "SortData", "SortComparer", "Header")):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"Type {ti}: {tname} (namespace='{get_mstr(tu[1])}', parent={tu[3]}, declaring={tu[4]}, m_cnt={m_cnt})")

# Also find any type whose declaring type is StreamedListView (33022) or StreamedTable (33080)
# Wait let's check which tu field is declaringTypeIndex
streamed_ti = set()
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    if tname in ("StreamedListView", "StreamedTable"):
        streamed_ti.add(ti)
        print(f"  {tname} ti={ti}, tu={tu}")

# Check all methods in FM.UI.dll around StreamedListView (methods near 0x015a3000..0x015f5000)
print("\n=== Methods in RVA range 0x015a3000 .. 0x015f3000 ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015a3000 <= rva <= 0x015f3000:
        names = rva_to_method_name[rva]
        if any(any(x in n for x in ("Sort", "Header", "Column", "Streamed")) for n in names):
            print(f"  0x{rva:08x}: {', '.join(names)}")

dump_func_details("StreamedTable.SetSorting(2) FULL", 0x015efce0, 0x015eff70 - 0x015efce0)
dump_func_details("StreamedTable.SortDataFromView FULL", 0x015eff70, 0x015f0040 - 0x015eff70)
dump_func_details("StreamedTable.MakeColumnHeader", 0x015eac30)
dump_func_details("StreamedTable.BindHeader", 0x015e6230)
dump_func_details("StreamedTable.OnHeaderClicked", 0x015ec910)
