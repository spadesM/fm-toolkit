import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, types_off, fields_off, dump_func_details
from annotate_sorting_usym import dump_annotated, literals, usym_map

# In IL2CPP global-metadata.dat v31:
# Let's check Il2CppType table in GameAssembly.dll (Il2CppMetadataRegistration) to resolve tag=1 (TypeInfo) and tag=2 (Il2CppType)!
# Wait: we can also check where StreamedListView fields are used across ALL StreamedListView and StreamedTable methods!

# Let's list all methods of StreamedListView and StreamedTable with their RVAs
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if n.startswith("StreamedListView.") or n.startswith("StreamedTable.") or "ScoutPriorit" in n or "SpecificallyScouted" in n:
            sz = rva_to_end.get(rva, rva + 64) - rva
            print(f"0x{rva:08x} (sz={sz:4d}): {n}")
