import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import rva_to_method_name, dump_func_details

dump_func_details("StreamedListView.set_Reorderable", 0x015ad4f0, 0x100)
dump_func_details("StreamedTable.InitialiseColumns", 0x015ea870, 0x600)
dump_func_details("StreamedTable.BindHeader", 0x015e6230, 0x450)
dump_func_details("StreamedTable.MakeHeader", 0x015eaee0, 0x450)

for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if "StreamedTable." in n or "StreamedListView." in n or "UxmlSerializedData.Deserialize" in n:
            if any(k in n for k in ("Header", "Sort", "Column", "Deserialize", "Reorder", "Drag")):
                print(f"  0x{rva:08x}: {n}")
