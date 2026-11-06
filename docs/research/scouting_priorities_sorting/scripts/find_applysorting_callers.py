import sys, struct, bisect
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, pe, va_to_off, off_to_va, image_base, rva_to_end

targets = {
    0x015a4260: "StreamedListView.ApplySorting",
    0x015ab800: "StreamedListView.UpdateSortingBinding",
    0x015e58c0: "StreamedTable.ApplyPersistedSortingState",
    0x015f0040: "StreamedTable.TrySetColumnsAndSort",
    0x015ef750: "StreamedTable.SetNoSorting",
    0x015a99d0: "StreamedListView.SetNoSorting",
}

sorted_starts = sorted(rva_to_end.keys())
start_off = va_to_off(image_base + 0x014b0000)
end_off = va_to_off(image_base + 0x016b0000)
for op in (b"\xE8", b"\xE9"):
    pos = start_off
    while True:
        pos = pe.find(op, pos, end_off)
        if pos == -1:
            break
        disp = struct.unpack_from("<i", pe, pos + 1)[0]
        rva = off_to_va(pos) - image_base
        t_rva = rva + 5 + disp
        if t_rva in targets:
            idx = bisect.bisect_right(sorted_starts, rva) - 1
            f_start = sorted_starts[idx] if idx >= 0 else 0
            f_names = rva_to_method_name.get(f_start, ["unknown"])
            print(f"Call to {targets[t_rva]} from RVA 0x{rva:08x} in 0x{f_start:08x} ({', '.join(f_names[:3])})")
        pos += 1
