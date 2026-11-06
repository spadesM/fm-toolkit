import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, pe, va_to_off, off_to_va, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end, rva_to_method_name

# Find which method contains 0x00468bb7
all_starts = sorted(rva_to_end.keys())
import bisect
for target_rva in [0x00468bb7, 0x00468c2d, 0x0046b097, 0x0046cb53]:
    idx = bisect.bisect_right(all_starts, target_rva) - 1
    m_rva = all_starts[idx]
    print(f"RVA 0x{target_rva:08x} is in method at 0x{m_rva:08x}: {rva_to_method_name.get(m_rva)} (end=0x{rva_to_end[m_rva]:08x})")

# Also check all 7 FourCCs of SpecificallyScoutedPersonReference in that method:
# 'rylp' (0x706c7972), 'axMd' (0x644d7861), 'EEYc' (0x63594545), '3cDu' (0x75446333), 'vLuq' (0x71754c76), ' Nqs' (0x73714e20), 'sWGn' (0x6e475773)
for fcc in [b"rylp", b"axMd", b"EEYc", b"3cDu", b"vLuq", b" Nqs", b"sWGn"]:
    pos = va_to_off(image_base + 0x00460000)
    end_pos = va_to_off(image_base + 0x00475000)
    idx = pe.find(fcc, pos, end_pos)
    while idx != -1:
        rva = off_to_va(idx) - image_base
        print(f"\nFourCC {fcc!r} at RVA 0x{rva:08x}:")
        # dump 64 bytes before and 96 bytes after
        s_rva = rva - 32
        off = va_to_off(image_base + s_rva)
        chunk = pe[off:off+128]
        # look for RIP-relative loads (48 8b 05 / 48 8b 0d / 48 8b 15)
        for i in range(len(chunk)-7):
            if chunk[i] == 0x48 and chunk[i+1] == 0x8b and chunk[i+2] in (0x05, 0x0d, 0x15, 0x1d, 0x35, 0x3d):
                rel = struct.unpack_from("<i", chunk, i+3)[0]
                rip_target = s_rva + i + 7 + rel
                print(f"  +0x{i:02x} (0x{s_rva+i:08x}): RIP load -> 0x{rip_target:08x}")
        idx = pe.find(fcc, idx + 1, end_pos)
