import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, off_to_va, va_to_off, image_base
from check_j1ct_and_nth_prop import resolve_data_rva

funcs = [
    ("StreamedListView.ApplySorting", 0x015a4260, 0x4c0),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x160),
    ("StreamedListView.BindToData", 0x015a49b0, 0x350),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x310),
    ("StreamedTable.OnBindItem", 0x015eb760, 0x360),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580, 0x280),
]

for name, rva, sz in funcs:
    print(f"\n=== {name} (0x{rva:08x}) ===")
    off = va_to_off(image_base + rva)
    chunk = pe[off : off + sz]
    for i in range(len(chunk) - 7):
        # Check for RIP-relative mov/lea:
        # 48 8b 05/0d/15/1d/2d/35/3d disp32
        # 4c 8b 05/0d/15/1d/25/2d/35/3d disp32
        b0, b1, b2 = chunk[i], chunk[i+1], chunk[i+2]
        if b0 in (0x48, 0x4c) and b1 in (0x8b, 0x8d) and (b2 & 0xc7) == 0x05:
            disp = struct.unpack_from("<i", chunk, i + 3)[0]
            insn_rva = rva + i
            trva = insn_rva + 7 + disp
            if 0x02a00000 <= trva <= 0x03500000:
                print(f"  +0x{i:03x}: RIP -> 0x{trva:08x} ({resolve_data_rva(trva)})")
        elif b1 in (0x8b, 0x8d) and (b2 & 0xc7) == 0x05 and b0 not in (0x48, 0x4c):
            # 3-byte RIP-relative without REX? No, 8b 05 disp32 starts at i+1
            pass
