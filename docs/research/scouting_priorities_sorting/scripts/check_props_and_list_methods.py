import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, types_off, types_sz, methods_off, fields_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_end, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

print("=== Methods in 0x004c5000..0x004c9000 and 0x004d2000..0x004d5000 ===")
for rva in sorted(rva_to_method_name.keys()):
    if (0x004c5000 <= rva <= 0x004c9000) or (0x004d2000 <= rva <= 0x004d5000):
        print(f"  0x{rva:08x}..0x{rva_to_end.get(rva, 0):08x}: {rva_to_method_name[rva]}")

# Disassemble functions around 0x004c7e00..0x004c8300 and 0x004d2200..0x004d4000
for rva in sorted(rva_to_method_name.keys()):
    if (0x004c7a00 <= rva <= 0x004c8500) or (0x004d2200 <= rva <= 0x004d4000):
        dump_annotated(f"{rva_to_method_name[rva][0]}", rva)

# Also if 0x4d370a / 0x4d3a90 are in functions not in rva_to_method_name (or in a function starting earlier), let's check!
for h in (0x4c7e92, 0x4c80b4, 0x4d28f2, 0x4d2c26, 0x4d370a, 0x4d38d4, 0x4d3a90):
    cands = [r for r in rva_to_end if r <= h]
    fn = max(cands) if cands else h
    print(f"Hit 0x{h:08x} -> closest fn 0x{fn:08x}..0x{rva_to_end.get(fn, 0):08x}: {rva_to_method_name.get(fn)}")

dump_func_details("Around 0x004d3600..0x004d3f00", 0x004d3600, 0x900)
dump_func_details("Around 0x004c7d00..0x004c8300", 0x004c7d00, 0x600)

targets = [
    ("StreamedListView.OnBindItemInternal", 0x015a67d0),
    ("StreamedListView.OnMoveItemInternal", 0x015a7480),
    ("StreamedListView.OnRebindItemInternal", 0x015a7660),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedListView.Refresh", 0x015a9390),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.GetBindingKind", 0x015e9cf0),
    ("StreamedTable.GetContexts", 0x015ea140),
    ("StreamedTable.GetIdentifiers", 0x015ea360),
    ("VirtualisedList.set_Reorderable", 0x014dada0),
    ("VirtualisedList.Refresh", 0x016a93f0),
    ("VirtualisedList.Rebuild", 0x016a9350),
    ("VirtualisedList.UpdateView", 0x016aa730),
    ("StreamedListView..ctor", 0x015abdf0),
    ("StreamedTable..ctor", 0x015f1930),
]

for name, rva in targets:
    dump_annotated(name, rva)
