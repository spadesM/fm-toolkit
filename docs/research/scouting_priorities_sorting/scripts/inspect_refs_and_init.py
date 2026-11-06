import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, types_off, types_sz, methods_off, get_mstr, va_to_off,
    image_base, rva_to_method_name, rva_to_end, dump_func_details
)
from annotate_sorting_usym import dump_annotated

# 1. Dump all methods of Type [6298..6305]
for ti in range(6298, 6306):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    mstart = tu[9]
    mcnt = tu[16] & 0xFFFF
    print(f"\n=== Type [{ti}] {tname} (methods={mcnt}) ===")
    for mi in range(mstart, mstart + mcnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        for rva, names in rva_to_method_name.items():
            if f"{tname}.{mname}" in names:
                sz = rva_to_end.get(rva, rva + 256) - rva
                dump_annotated(f"{tname}.{mname}", rva, sz)
                dump_func_details(f"{tname}.{mname}", rva, sz)
