import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# Let's check Il2CppTypeDefinition field offsets from Il2CppRegistration!
# Wait: let's also check what methods are at 0x00e030e0, 0x00a28920, 0x00a28ae0, 0x015e9450, 0x015f1380
for rva in (0x00e030e0, 0x00a28920, 0x00a28ae0, 0x015e9450, 0x015f1380):
    print(f"RVA 0x{rva:08x}: {rva_to_method_name.get(rva)}")

# Let's list all fields of StreamedTable, StreamedListView, VirtualisedList, and Entry in SI.Bindable.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname != "SI.Bindable.dll":
        continue
    t_start, t_cnt = iu[2], iu[3]
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname in ("StreamedTable", "StreamedListView", "VirtualisedList", "Entry", "Column", "Header"):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            print(f"\n=== Type {ti}: {tname} ({f_cnt} fields) ===")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                print(f"  Field {fi - f_start}: {get_mstr(fu[0])}")
