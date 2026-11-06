import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr
from annotate_sorting_usym import dump_annotated

# 1. Check 0x00abdcc0 (called by SetSortingBinding)
print("0x00abdcc0:", rva_to_method_name.get(0x00abdcc0))
dump_annotated("func_0x00abdcc0", 0x00abdcc0)
dump_func_details("func_0x00abdcc0", 0x00abdcc0)

# 2. Check StreamedListView.BindToDataInternal full function (find start RVA)
for rva, name in sorted(rva_to_method_name.items()):
    if "StreamedListView." in name and ("Bind" in name or "State" in name or "Sort" in name or "Build" in name or "Item" in name):
        print(f"  0x{rva:08x}: {name}")

print("\nStreamedTable methods with State/Sort/Bind/Build/Init/View:")
for rva, name in sorted(rva_to_method_name.items()):
    if "StreamedTable." in name:
        print(f"  0x{rva:08x}: {name}")
