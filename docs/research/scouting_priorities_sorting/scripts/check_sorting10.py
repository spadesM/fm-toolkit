import sys
from dump_headers_fast import dump_fast, get_usym_dict
from check_deep_sorting import rva_to_end, rva_to_method_name

with open("sorting_disasm10.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    targets = [
        ("StreamedTable_0x015f1760 (cs:2333)", 0x015f1760),
        ("StreamedTable_0x015ef1e0 (cs:2377)", 0x015ef1e0),
        ("StreamedTable_0x015e9f40 (cs:3324)", 0x015e9f40),
        ("StreamedTable_0x015eead0 (cs:1952)", 0x015eead0),
        ("StreamedTable_0x015e9220 (cs:1930)", 0x015e9220),
        ("StreamedTable_0x015f0f50 (cs:1922)", 0x015f0f50),
        ("StreamedListView_0x015a9ee0 (cs:1911)", 0x015a9ee0),
        ("StreamedListView_0x015aab80 (cs:705)", 0x015aab80),
        ("StreamedListView_0x015ab4a0 (cs:1518)", 0x015ab4a0),
        ("Bindings.GetNthProperty", 0x014c1450),
        ("Bindings.RemoveFirstProperty", 0x014c1a60),
        ("Bindings.CreateScope", 0x014bf980),
        ("Bindings.OpenChannel", 0x014c3050),
    ]

    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x400)
        dump_fast(name, rva, min(end_rva, rva + 0x800))

    print("\n=== ALL StreamedListView / StreamedTable / VirtualisedList methods ===")
    for rva in sorted(rva_to_end.keys()):
        if 0x015a0000 <= rva <= 0x015f5000:
            end_rva = rva_to_end[rva]
            mname = rva_to_method_name.get(rva, "")
            umap = get_usym_dict(rva, end_rva - rva)
            srcs = []
            for k in sorted(umap.keys()):
                srcs.extend(umap[k])
            src_str = srcs[0] if srcs else ""
            if "StreamedListView" in src_str or "StreamedTable" in src_str or "VirtualisedList" in src_str or mname:
                print(f"  0x{rva:08x} - 0x{end_rva:08x}: {mname} | {src_str}")
