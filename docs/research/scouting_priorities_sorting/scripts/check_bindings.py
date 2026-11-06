import sys
from dump_headers_fast import (
    dump_fast, pe, meta, image_base, va_to_off, resolve_rip, get_mstr,
    types_off, types_sz, methods_off, methods_sz, hdr
)
from check_deep_sorting import rva_to_end, rva_to_method_name

with open("sorting_disasm16.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    targets = [
        ("Bindings.CreateGroup", 0x014bf980),
        ("Bindings.MakeScope", 0x014c3050),
        ("Bindings.Register", 0x014bee30),
        ("Bindings.Unregister", 0x014c63d0),
        ("Bindings.Set", 0x014c5740),
    ]
    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x200)
        dump_fast(name, rva, min(end_rva, rva + 0x1000))

    print("\n=== Metadata RIPs ===")
    for name, rip in [
        ("tag=2, idx=32982", 0x02e06ea8),
        ("tag=1, idx=38755", 0x02e37848),
        ("tag=6, idx=184959", 0x02e21500),
        ("tag=1, idx=26734", 0x02df8a38),
        ("tag=1, idx=37208", 0x02e1aab8),
        ("tag=1, idx=23672", 0x02e4d5e0),
        ("tag=1, idx=23676", 0x02e4d840),
        ("tag=1, idx=56117", 0x02e1c298),
        ("tag=6, idx=209012", 0x02e10d28),
        ("tag=6, idx=189930", 0x02e07f68),
    ]:
        print(f"{name} (0x{rip:08x}) -> {resolve_rip(rip)}")
