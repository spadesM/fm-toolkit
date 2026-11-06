import struct, sys, json
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name, modules, images_off, images_sz

with open("sorting_disasm15.txt", "w", encoding="utf-8") as f:
    sys.stdout = f

    targets = [
        ("SortComparer.Compare", 0x015a3d30),
        ("SortingData.GetCell", 0x015a3fc0),
        ("SortingData.GetValue", 0x015a4000),
        ("SortingData.HasReceived", 0x015a4040),
        ("Bindings.GetPropertyAtDepth", 0x014c1450),
        ("Bindings.RemoveFirstProperty", 0x014c1a60),
        ("Func_0x00b01190", 0x00b01190),
        ("Hash_0x0129faf0", 0x0129faf0),
        ("AutogenBindings_0x002ae590", 0x002ae590),
    ]
    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x200)
        dump_fast(name, rva, min(end_rva, rva + 0x1000))

    with open("table_Investigation.json", "r", encoding="utf-8") as jf:
        tinv = json.load(jf)
    print("\n=== Table Views & Factories Summary ===")
    print(json.dumps(tinv, indent=2))
