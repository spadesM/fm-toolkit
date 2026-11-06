import struct
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, dump_func_details, get_mstr, methods_off, types_off, types_sz
from annotate_sorting_usym import dump_annotated

print("Method at 0x00af20c0:", rva_to_method_name.get(0x00af20c0))
dump_annotated("sub_00af20c0", 0x00af20c0, rva_to_end.get(0x00af20c0, 0x00af21c0) - 0x00af20c0)
dump_func_details("sub_00af20c0", 0x00af20c0, rva_to_end.get(0x00af20c0, 0x00af21c0) - 0x00af20c0)
dump_annotated("StreamedListView.ApplySorting", 0x015a4260)
dump_annotated("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320)
dump_annotated("StreamedListView.BindSortPathNextDepth", 0x015a4850)
dump_annotated("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0)
dump_annotated("StreamedTable.BindToDataInternal", 0x015e6d70)
