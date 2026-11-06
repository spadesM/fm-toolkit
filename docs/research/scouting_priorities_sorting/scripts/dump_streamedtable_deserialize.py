import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import dump_func_details, pe, va_to_off, image_base, rva_to_method_name

dump_func_details("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0, 0x600)
dump_func_details("StreamedTable.CreateHeader", 0x015e8f00, 0x200)
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x350)

# Also check what fields StreamedListView.UxmlSerializedData.Deserialize sets around Reorderable!
# Let's check all field offsets of StreamedListView and StreamedTable from metadata!
from check_deep_sorting import types_off, types_sz, fields_off, get_mstr, meta
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    ns = get_mstr(tu[1])
    if tname in ("StreamedListView", "StreamedTable", "UxmlSerializedData") and ("Bindable" in ns or tname == "UxmlSerializedData"):
        f_start, f_cnt = tu[7], tu[17] & 0xFFFF
        fnames = [get_mstr(struct.unpack_from("<2i", meta, fields_off + (f_start + fi) * 16)[0]) for fi in range(f_cnt)]
        if any("Sort" in fn or "Reorder" in fn or "Drag" in fn for fn in fnames):
            print(f"\nType #{ti} {ns}.{tname} (fields={f_cnt}):")
            for fi, fn in enumerate(fnames):
                print(f"  [{fi}] {fn}")
