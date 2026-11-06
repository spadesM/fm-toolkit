import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, off_to_va, image_base, dump_func_details,
    types_off, methods_off, fields_off, get_mstr
)

# Let's check how meta_usage is decoded in GameAssembly.dll / global-metadata.dat
# Also let's dump StreamedListView.SetSortingBinding (0x015a9ae0) and ProcessSortingDataChanged (0x015a8cb0..0x015a9050)
dump_func_details("StreamedListView.SetSortingBinding (0x015a9a80)", 0x015a9a80, 0x180)
dump_func_details("StreamedListView.ProcessSortingDataChanged_PART2", 0x015a8e50, 0x220)
dump_func_details("SortData.HasReceived (0x015a4040)", 0x015a4040, 0x220)
dump_func_details("RowComparer.Compare", 0x015a3b00, 0x540)
