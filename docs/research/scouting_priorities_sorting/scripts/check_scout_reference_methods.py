import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr, methods_off, types_off, types_sz
from annotate_sorting_usym import dump_annotated

print("Matching methods in rva_to_method_name for ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference:")
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(k in n for k in ["ScoutPlayerPriorities", "SpecificallyScoutedPerson", "ScoutPriorities", "BindToDataInternal", "ApplySorting", "BindSortPathNextDepth", "ProcessSortingDataChanged"]):
            print(f"  0x{rva:08x}: {n}")

# Dump the getters of ScoutPlayerPrioritiesReference and SpecificallyScoutedPersonReference
for rva in [0x0067d3d0, 0x0067d460, 0x0067d510, 0x006970a0, 0x006970b0, 0x006970c0, 0x006970f0, 0x00697120, 0x00697150, 0x00697160]:
    names = rva_to_method_name.get(rva, [f"sub_{rva:08x}"])
    end_rva = rva_to_end.get(rva, rva + 0x100)
    dump_func_details(names[0], rva, end_rva - rva)

# Dump StreamedListView sorting methods
for name, rva in [
    ("StreamedListView.ApplySorting", 0x015a4260),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
]:
    end_rva = rva_to_end.get(rva, rva + 0x600)
    dump_func_details(name, rva, end_rva - rva)
