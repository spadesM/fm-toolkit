import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va

method_rvas = sorted(rva_to_method_name.keys())

def rva_to_off(rva):
    return va_to_off(image_base + rva)

def off_to_rva(off):
    return off_to_va(off) - image_base

print("=== 1. Check all methods of VirtualisedList and StreamedTable/StreamedListView for Reorderable / Drag ===")
for rva, m_list in sorted(rva_to_method_name.items()):
    matched = [m for m in m_list if any(k in m for k in ['Reorderable', 'DragCell', 'BindHeader', 'SetupClickHandler', 'MakeColumnHeader'])]
    if matched:
        print(f"  0x{rva:08x}: {', '.join(matched)}")

print("\n=== 2. Check callers of get_Reorderable (0x015acd60), VirtualisedList.get_Reorderable (0x014dad90), and get_IsDragCellActive (0x015f2230) ===")
text_off = rva_to_off(0x01400000)
text_end = rva_to_off(0x01800000)

for target_rva, name in [
    (0x015acd60, 'StreamedListView.get_Reorderable'),
    (0x014dad90, 'VirtualisedList.get_Reorderable'),
    (0x015f2230, 'StreamedTable.get_IsDragCellActive'),
]:
    print(f"Callers of {name} (0x{target_rva:08x}):")
    for p in range(text_off, text_end - 5):
        b = pe[p]
        if b in (0xE8, 0xE9):
            rel = struct.unpack_from('<i', pe, p + 1)[0]
            call_rva = off_to_rva(p)
            if call_rva + 5 + rel == target_rva:
                idx = bisect.bisect_right(method_rvas, call_rva) - 1
                m_rva = method_rvas[idx] if idx >= 0 else 0
                print(f"  0x{call_rva:08x} in {rva_to_method_name.get(m_rva, ['unknown'])[:4]}")

print("\n=== 3. Check 7 properties of SpecificallyScoutedPersonReference (0x7443314a) ===")
prop_fourccs = [0x706c7972, 0x644d7861, 0x63594545, 0x75446333, 0x71754c76, 0x73714e20, 0x6e475773]
for fcc in prop_fourccs:
    pat = b'\xb9' + struct.pack('<I', fcc)
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_rva(idx)
        m_idx = bisect.bisect_right(method_rvas, rva) - 1
        m_rva = method_rvas[m_idx] if m_idx >= 0 else 0
        m_name = rva_to_method_name.get(m_rva, ['unknown'])[:3]
        strs = []
        for s_off in range(idx - 64, idx + 64):
            if pe[s_off:s_off+3] in (b'\x48\x8b\x05', b'\x48\x8b\x0d', b'\x48\x8b\x15', b'\x4c\x8b\x05', b'\x4c\x8b\x0d'):
                disp = struct.unpack_from('<i', pe, s_off + 3)[0]
                target_va = image_base + off_to_rva(s_off) + 7 + disp
                info = resolve_rip_va(target_va)
                if info and 'STR' in info:
                    strs.append((s_off - idx, info))
        print(f"  FourCC 0x{fcc:08x} ({struct.pack('<I', fcc)!r}) at 0x{rva:08x} in {m_name}: {strs}")
        pos = idx + 1

print("\n=== 4. Search for FourCC 0x724c4e4d ('MNLr' = SpecificallyScoutedPlayers) in .text ===")
pat_mnlr = struct.pack('<I', 0x724c4e4d)
pos = 0
while True:
    idx = pe.find(pat_mnlr, pos)
    if idx == -1:
        break
    rva = off_to_rva(idx)
    m_idx = bisect.bisect_right(method_rvas, rva) - 1
    m_rva = method_rvas[m_idx] if m_idx >= 0 else 0
    print(f"  0x724c4e4d at 0x{rva:08x} in {rva_to_method_name.get(m_rva, ['unknown'])[:4]}")
    pos = idx + 1
