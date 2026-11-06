import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes
from check_deep_sorting import pe, meta, images_off, images_sz, types_off, fields_off, get_mstr

# Let's get the exact field names of VisualElement.UxmlSerializedData, BindableVisualElement.UxmlSerializedData, StreamedListView.UxmlSerializedData, StreamedTable.UxmlSerializedData
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in ("UnityEngine.UIElementsModule.dll", "SI.Bindable.dll"):
        continue
    t_start, t_cnt = iu[2], iu[3]
    prev_tname = ""
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname == "UxmlSerializedData" and prev_tname in ("VisualElement", "BindableVisualElement", "StreamedListView", "StreamedTable"):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            fnames = [get_mstr(struct.unpack_from("<3i", meta, fields_off + fi * 12)[0]) for fi in range(f_start, f_start + f_cnt)]
            print(f"=== {prev_tname}.UxmlSerializedData (Type {ti}, {f_cnt} fields) ===")
            for idx, fn in enumerate(fnames):
                print(f"  {idx:2d}: {fn}")
        if tname != "UxmlSerializedData":
            prev_tname = tname

# Also let's compare byte-by-byte the first 0x200 bytes of StreamedTable/UxmlSerializedData across Obj 229, 263, 111, 297, 360
print("\n=== Comparing first 0x120 bytes of StreamedTable/UxmlSerializedData ===")
objs_data = {}
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    objs_data[oi] = (name, dbytes)
    print(f"\nObj {oi} ({name}):")
    for off in range(0, min(0x120, len(dbytes)), 16):
        chunk = dbytes[off:off+16]
        print(f"  +0x{off:03x}: {chunk.hex(' ')}")
