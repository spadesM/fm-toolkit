import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# 1. List all types in SI.Bindable.dll from 5970 to end of SI.Bindable.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname != "SI.Bindable.dll":
        continue
    t_start, t_cnt = iu[2], iu[3]
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        ns = get_mstr(tu[1])
        if any(w in tname.lower() for w in ("table", "factory", "header", "column", "sort", "virtual", "list")):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            fnames = [get_mstr(struct.unpack_from("<3i", meta, fields_off + fi * 12)[0]) for fi in range(f_start, f_start + f_cnt)]
            print(f"Type {ti}: {ns}.{tname} -> fields={fnames}")

# 2. Check what functions are at or near 0x00e030e0, 0x00a28920, 0x00a28ae0, 0x00e6d530, 0x015106c0
for target in (0x00e030e0, 0x00a28920, 0x00a28ae0, 0x00e6d530, 0x015106c0):
    # Find closest method RVA <= target
    best_rva = max((r for r in rva_to_method_name if r <= target), default=0)
    print(f"Target 0x{target:08x} -> closest method RVA 0x{best_rva:08x}: {rva_to_method_name.get(best_rva)}")
    dump_func_details(f"Func_0x{target:08x}", target, 0x120)
