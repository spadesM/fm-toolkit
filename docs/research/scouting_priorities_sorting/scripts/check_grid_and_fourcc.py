import struct, sys, bisect, json
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details, root
)
from check_refs_and_grid import inspect_bundle

# 1. Inspect ui-tileslayouts_assets_all.bundle for pathID = 7661162286614362349
inspect_bundle("ui-tileslayouts_assets_all.bundle", target_pids={7661162286614362349})

# 2. Scan ALL executable sections for callers of sorting methods
targets = {
    0x015ef750: "StreamedTable.SetNoSorting",
    0x015a99d0: "StreamedListView.SetNoSorting",
    0x015f2420: "StreamedTable.set_DisableSorting",
    0x015efc40: "StreamedTable.SetSorting(col,dir,notify)",
    0x015efce0: "StreamedTable.SetSorting(prop,dir,notify)",
    0x015a9a80: "StreamedListView.SetSortingBinding(prop)",
    0x015a9ae0: "StreamedListView.SetSortingBinding(dict)",
}
print("\n=== Scanning ALL sections for callers of sorting control methods ===")
func_starts = sorted(rva_to_end.keys())
for sec_name, vaddr, vsize, raddr, rsize in sections:
    if sec_name not in (".text", "il2cpp"):
        continue
    s_bytes = pe[raddr : raddr + rsize]
    for op_byte in (b"\xe8", b"\xe9"):
        pos = 0
        while True:
            idx = s_bytes.find(op_byte, pos)
            if idx == -1 or idx > len(s_bytes) - 5:
                break
            pos = idx + 1
            disp = struct.unpack_from("<i", s_bytes, idx + 1)[0]
            call_rva = vaddr + idx
            tgt_rva = call_rva + 5 + disp
            if tgt_rva in targets:
                fidx = bisect.bisect_right(func_starts, call_rva) - 1
                fn_start = func_starts[fidx] if fidx >= 0 else call_rva
                fn_names = rva_to_method_name.get(fn_start, [f"sub_{fn_start:08x}"])
                print(f"  [{sec_name}] 0x{call_rva:08x} (in {fn_names[0]} @ 0x{fn_start:08x}) -> {targets[tgt_rva]}")

# 3. Search PE for FourCCs 0x644d7861 (dMxa) and 0x67393649 (g96I)
for label, pat in [("dMxa (0x644d7861)", b"\x61\x78\x4d\x64"), ("g96I (0x67393649)", b"\x49\x36\x39\x67"), ("fFcK (0x6646634b)", b"\x4b\x63\x46\x66")]:
    print(f"\n=== Occurrences of {label} ===")
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        pos = idx + 1
        va = off_to_va(idx)
        rva = va - image_base if va else 0
        fidx = bisect.bisect_right(func_starts, rva) - 1
        fn_start = func_starts[fidx] if fidx >= 0 and rva < rva_to_end.get(func_starts[fidx], 0) else 0
        fn_names = rva_to_method_name.get(fn_start, [f"sub_{fn_start:08x}"]) if fn_start else ["data"]
        print(f"  off=0x{idx:x} RVA=0x{rva:08x} in {fn_names[0]} (0x{fn_start:08x})")
