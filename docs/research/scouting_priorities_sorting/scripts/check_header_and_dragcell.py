import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

dump_func_details("StreamedTable.CreateColumns", 0x015e83b0, 0x600)
dump_func_details("StreamedTable.CreateHeader", 0x015e8f00, 0x200)
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x450)
dump_func_details("StreamedTable.get_IsDragCellActive", 0x015f2230, 0x100)
dump_func_details("StreamedTable.SetSorting_1 (0x015efc40)", 0x015efc40, 0xa0)
dump_func_details("StreamedTable/UxmlSerializedData.Deserialize (0x015f36b0)", 0x015f36b0, 0x600)
