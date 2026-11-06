import struct, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details, root
)

# 1. Disassemble ScoutPlayerPrioritiesReference & SpecificallyScoutedPersonReference methods
dump_func_details("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360)
dump_func_details("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80)
dump_func_details("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200)

# 2. Find all CALL/JMP instructions in .text targeting SetNoSorting (0x015ef750, 0x015a99d0) or set_DisableSorting (0x015f2420)
targets = {
    0x015ef750: "StreamedTable.SetNoSorting",
    0x015a99d0: "StreamedListView.SetNoSorting",
    0x015f2420: "StreamedTable.set_DisableSorting",
    0x015efc40: "StreamedTable.SetSorting(col,dir,notify)",
    0x015efce0: "StreamedTable.SetSorting(prop,dir,notify)",
    0x015a9a80: "StreamedListView.SetSortingBinding(prop)",
    0x015a9ae0: "StreamedListView.SetSortingBinding(dict)",
}
print("\n=== Scanning for callers of sorting control methods ===")
from check_deep_sorting import sections
text_sec = [s for s in sections if s[0] == ".text"][0]
t_vaddr, t_vsize, t_raddr, t_rsize = text_sec[1], text_sec[2], text_sec[3], text_sec[4]
t_bytes = pe[t_raddr : t_raddr + t_rsize]

# Build sorted list of function start RVAs for lookup
import bisect
func_starts = sorted(rva_to_end.keys())

for i in range(len(t_bytes) - 5):
    b = t_bytes[i]
    if b in (0xE8, 0xE9):
        disp = struct.unpack_from("<i", t_bytes, i + 1)[0]
        call_rva = t_vaddr + i
        tgt_rva = call_rva + 5 + disp
        if tgt_rva in targets:
            idx = bisect.bisect_right(func_starts, call_rva) - 1
            fn_start = func_starts[idx] if idx >= 0 else call_rva
            fn_names = rva_to_method_name.get(fn_start, [f"sub_{fn_start:08x}"])
            print(f"  0x{call_rva:08x} (in {fn_names[0]} @ 0x{fn_start:08x}) -> {targets[tgt_rva]}")

# 3. Find bundle containing CAB-ee9fb57ee732c9abd565f5c4171f2bad
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
for bfile in aa_dir.glob("*.bundle"):
    raw_head = bfile.read_bytes()[:4096]
    if b"CAB-ee9fb57ee732c9abd565f5c4171f2bad" in raw_head:
        print(f"\nFound CAB-ee9fb57ee732c9abd565f5c4171f2bad in: {bfile.name}")
