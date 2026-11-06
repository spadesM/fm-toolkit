import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, methods_sz, types_off, types_sz, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va

def rva_to_off(rva):
    return va_to_off(image_base + rva)

def off_to_rva(off):
    return off_to_va(off) - image_base

print("=== 1. Dump BindSortPathNextDepth (0x015a4850) and ProcessSortingDataChanged (0x015a8cb0) ===")
for name, rva in [
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.Sort", 0x015a9ae0),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva, rva_to_end.get(rva, rva + 256) - rva)

print("\n=== 2. Dump ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference methods ===")
for name, rva in [
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360),
    ("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
]:
    dump_func_details(name, rva, rva_to_end.get(rva, rva + 256) - rva)
