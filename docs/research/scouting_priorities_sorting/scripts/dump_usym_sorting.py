import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Enhance get_usym_dict to also include symbol name (sym_off) and parent symbol!
def get_usym_full(target_rva, span):
    lo, hi = 0, dhf.sym_count - 1
    while lo < hi:
        mid = (lo + hi) // 2
        rva = struct.unpack_from("<I", dhf.udata, dhf.records_off + mid * 24)[0]
        if rva < target_rva: lo = mid + 1
        else: hi = mid
    res = {}
    for idx in range(max(0, lo - 2), min(dhf.sym_count, lo + 500)):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", dhf.udata, dhf.records_off + idx * 24)
        if rva > target_rva + span: break
        if rva >= target_rva:
            fn = dhf.get_ustr(file_off).split("/")[-1].split("\\")[-1]
            sym = dhf.get_ustr(sym_off)
            res.setdefault(rva, []).append(f"{sym} ({fn}:{line})")
    return res

dhf.get_usym_dict = get_usym_full

targets = [
    ("Bindings.GetDepth", 0x014c1310, 0x014c1450),
    ("Bindings.GetNthProperty", 0x014c1450, 0x014c15b0),
    ("StreamedListView.ApplySorting", 0x015a4260, 0x015a4720),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x015aa631),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x015a49a6),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 0x015a8109),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a8ead),
    ("StreamedListView.TryOrderRows", 0x015a9dd0, 0x015a9f50),
    ("StreamedListView.FinalizeRowOrdering", 0x015a6080, 0x015a62a0),
    ("SortData.HasReceived", 0x015a4040, 0x015a40f0),
    ("SortData.SetData", 0x015a40f0, 0x015a41e0),
    ("SortData.SetExpected", 0x015a41e0, 0x015a4260),
    ("SortComparer.Compare(x,y)", 0x015a3c60, 0x015a3d30),
    ("SortComparer.Compare(a,b,dir,col)", 0x015a3d30, 0x015a3ec0),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x015f0230),
    ("Header..ctor", 0x015ed7f0, 0x015edc50),
]

for name, s, e in targets:
    dhf.dump_fast(name, s, e)
