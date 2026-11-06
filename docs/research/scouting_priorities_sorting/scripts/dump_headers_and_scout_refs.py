import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va

def rva_to_off(rva):
    return va_to_off(image_base + rva)

print("=== 1. Check methods of ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference ===")
for rva, m_list in sorted(rva_to_method_name.items()):
    matched = [m for m in m_list if any(k in m for k in ['ScoutPlayerPriorities', 'ScoutPriorities', 'SpecificallyScoutedPerson'])]
    if matched:
        print(f"  0x{rva:08x}: {', '.join(matched)}")

print("\n=== 2. Dump SpecificallyScoutedPersonReference.GetPropertiesInternal and GetPropertyValue ===")
for rva, m_list in sorted(rva_to_method_name.items()):
    for m in m_list:
        if 'SpecificallyScoutedPersonReference.' in m or 'ScoutPlayerPrioritiesReference.' in m or 'ScoutPrioritiesReference.' in m:
            dump_annotated(m, rva)

print("\n=== 3. Dump StreamedTable.BindHeader, BindHeaders, MakeColumnHeader, Header.SetupClickHandler ===")
dump_annotated("Header.SetupClickHandler", 0x015df7e0)
dump_annotated("StreamedTable.BindHeader", 0x015e6230)
dump_annotated("StreamedTable.BindHeaders", 0x015e6ca0)
dump_annotated("StreamedTable.MakeColumnHeader", 0x015eac30)
dump_annotated("<>c__DisplayClass234_0.<BindHeader>b__0", 0x0160b6b0)
dump_annotated("<>c__DisplayClass234_0.<BindHeader>b__2", 0x0160b850)
dump_annotated("<>c__DisplayClass234_1.<BindHeader>b__1", 0x0160b9e0)
dump_annotated("<>c__DisplayClass259_0.<MakeColumnHeader>b__0", 0x0160bb80)
