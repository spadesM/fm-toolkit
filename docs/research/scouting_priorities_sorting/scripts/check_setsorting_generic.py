import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name, pe, va_to_off, image_base

dump_func_details(f"sub_00abdcc0 ({rva_to_method_name.get(0x00abdcc0)})", 0x00abdcc0)

# Also check virtual methods at vtable offsets 0xd98, 0xda0, 0xda8, 0xe18 on StreamedListView / StreamedTable
# Let's check all methods of StreamedListView and VirtualisedList in check_deep_sorting
from check_deep_sorting import meta, images_off, images_sz, types_off, methods_off, fields_off, get_mstr, modules, rva_to_end

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("VirtualisedList", "StreamedListView", "StreamedTable", "SortData", "SortColumn"):
                f_start = tu[7]
                f_cnt = tu[17] & 0xFFFF
                print(f"\n=== Fields of {tname} (Type {ti}, count={f_cnt}) ===")
                for fi in range(f_start, f_start + f_cnt):
                    fu = struct.unpack_from("<2i", meta, fields_off + fi * 8)
                    fname = get_mstr(fu[0])
                    print(f"  Field {fi - f_start}: {fname}")
