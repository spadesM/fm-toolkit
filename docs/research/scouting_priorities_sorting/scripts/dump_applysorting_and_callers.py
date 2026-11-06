import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, pe, meta, types_off, get_mstr, va_to_off, image_base, rva_to_end, rva_to_method_name

tu = struct.unpack_from("<22i", meta, types_off + 23779 * 88)
print("T(23779):", get_mstr(tu[1]), get_mstr(tu[0]))

dump_func_details("StreamedListView.ApplySorting", 0x015a4260, 0x350)
dump_func_details("StreamedListView.SetSortingBinding_1", 0x015a9a80, 0x60)
dump_func_details("StreamedListView.SetSortingBinding_2", 0x015a9ae0, 0x200)

# Find all callers of HasSorting (0x015a5f20), ApplySorting (0x015a4260), SetNoSorting (0x015a99d0), ClearSortingState (0x015a5180)
targets = {
    0x015a5f20: "HasSorting",
    0x015a4260: "ApplySorting",
    0x015a99d0: "SetNoSorting",
    0x015a5180: "ClearSortingState",
    0x015a9a80: "SetSortingBinding_1",
    0x015a9ae0: "SetSortingBinding_2",
}
for s_rva, e_rva in [(0x015a3000, 0x015b3000), (0x015df000, 0x01610000)]:
    off_s = va_to_off(image_base + s_rva)
    off_e = va_to_off(image_base + e_rva)
    chunk = pe[off_s:off_e]
    for i in range(len(chunk) - 5):
        if chunk[i] in (0xe8, 0xe9):
            disp = struct.unpack_from("<i", chunk, i + 1)[0]
            trva = s_rva + i + 5 + disp
            if trva in targets:
                caller_rva = s_rva + i
                fn_rva = max((k for k in rva_to_end if k <= caller_rva), default=0)
                print(f"Call to {targets[trva]} from 0x{caller_rva:08x} in {rva_to_method_name.get(fn_rva, [hex(fn_rva)])} (+0x{caller_rva-fn_rva:x})")
