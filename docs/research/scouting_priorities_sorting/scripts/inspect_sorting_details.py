import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
from check_deep_sorting import (
    pe, meta, image_base, va_to_off, rva_to_end, rva_to_method_name,
    get_mstr, methods_off, types_off, images_off, images_sz, modules, dump_func_details
)
from annotate_sorting_usym import dump_annotated, usym_map

hdr = struct.unpack_from("<64I", meta, 0)
byval_types_off, byval_types_sz = hdr[32], hdr[33]

# 1. List all methods of SortData, VirtualisedList, StreamedListView, StreamedTableView, StreamedTable
target_types = {"SortData", "VirtualisedList", "StreamedListView", "StreamedTableView", "StreamedTable"}
type_methods = {}
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in modules:
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname in target_types or "TableInit" in tname or "InitTable" in tname or "TableView" in tname:
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            mlist = []
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                mlist.append((mi, mname, rva, sz))
            type_methods[f"{iname}:{tname}({ti})"] = mlist

for k, mlist in type_methods.items():
    if any(x in k for x in ("SortData", "TableInit", "InitTable", "VirtualisedList")):
        print(f"=== {k} ===")
        for mi, mname, rva, sz in mlist:
            print(f"  [{mi}] {mname}: RVA=0x{rva:08x} size={sz}")

# 2. Scan all methods in VirtualisedList, StreamedListView, StreamedTableView, StreamedTable for 0x5c1 (c1 05 00 00) or calls to get_Reorderable
print("\n=== Scanning for 0x5c1 (Reorderable) and 0x9b8 (DisableSorting) ===")
for k, mlist in type_methods.items():
    for mi, mname, rva, sz in mlist:
        if rva == 0 or sz <= 0:
            continue
        off = va_to_off(image_base + rva)
        if off < 0:
            continue
        code = pe[off : off + sz]
        for pat, pat_name in [(b"\xc1\x05\x00\x00", "+0x5c1 (Reorderable)"), (b"\xb8\x09\x00\x00", "+0x9b8 (DisableSorting)"), (b"\xb0\x09\x00\x00", "+0x9b0 (SortedColumn)"), (b"\x40\x09\x00\x00", "+0x940 (m_initFunction)")]:
            idx = code.find(pat)
            while idx != -1:
                print(f"  {k}.{mname} (0x{rva:08x}) +0x{idx:03x}: refs {pat_name} -> {code[max(0, idx-4):idx+8].hex(' ')}")
                idx = code.find(pat, idx + 1)

# 3. Dump SortData.HasReceived, StreamedListView.ResetIndices, StreamedListView.UpdateEnabledState
dump_func_details("SortData.HasReceived", 0x015a4040)
dump_annotated("SortData.HasReceived", 0x015a4040)
dump_func_details("StreamedListView.ResetIndices", 0x015a9420)
dump_annotated("StreamedListView.ResetIndices", 0x015a9420)
dump_func_details("StreamedListView.UpdateEnabledState", 0x015aab80)
dump_annotated("StreamedListView.UpdateEnabledState", 0x015aab80)
dump_func_details("Bindings.Create", 0x014bf980)
dump_annotated("Bindings.Create", 0x014bf980)
dump_func_details("Bindings.Bind", 0x014bee30)
dump_annotated("Bindings.Bind", 0x014bee30)
