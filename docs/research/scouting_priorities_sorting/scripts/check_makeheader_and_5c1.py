import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va, usym_map
from investigate_sorting_diff import describe_il2cpp_type

def rva_to_off(rva):
    return va_to_off(image_base + rva)

def off_to_rva(off):
    return off_to_va(off) - image_base

print("=== 1. Check where +0x5c1 (m_reorderable on VirtualisedList) or +0x9b8 (m_disableSorting on StreamedTable) is read in [0x014b0000..0x016c0000] ===")
start_off = rva_to_off(0x014b0000)
end_off = rva_to_off(0x016c0000)
method_rvas = sorted(rva_to_method_name.keys())

for disp_bytes, label in [(b'\xc1\x05\x00\x00', '+0x5c1 (VirtualisedList.m_reorderable)'), (b'\xb8\x09\x00\x00', '+0x9b8 (StreamedTable.m_disableSorting)')]:
    print(f"Occurrences of {label}:")
    pos = start_off
    while True:
        idx = pe.find(disp_bytes, pos, end_off)
        if idx == -1:
            break
        rva = off_to_rva(idx)
        m_idx = bisect.bisect_right(method_rvas, rva) - 1
        m_rva = method_rvas[m_idx] if m_idx >= 0 else 0
        ctx = pe[idx-4:idx+6].hex(' ')
        print(f"  0x{rva:08x} (+0x{rva - m_rva:03x}) in {rva_to_method_name.get(m_rva, ['unknown'])[:3]}: {ctx}")
        pos = idx + 1

print("\n=== 2. Dump MakeColumnHeader (0x015eac30), <MakeColumnHeader>b__0 (0x0160bb80), Header..ctor (0x015dfab0), Header.Bind (0x015df4f0) ===")
for name, rva in [
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("<>c__DisplayClass259_0.<MakeColumnHeader>b__0", 0x0160bb80),
    ("Header..ctor", 0x015dfab0),
    ("Header.Bind", 0x015df4f0),
    ("Header.SetupClickHandler", 0x015df7e0),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva, rva_to_end.get(rva, rva + 256) - rva)
