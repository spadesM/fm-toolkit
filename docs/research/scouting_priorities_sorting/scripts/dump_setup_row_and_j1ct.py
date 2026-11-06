import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_apply_sorting_and_j1ct import dump_with_strings, resolve_data_rva
from check_deep_sorting import pe, image_base, va_to_off

dump_with_strings("StreamedListView.SetupRow (full)", 0x015aa320)
dump_with_strings("StreamedListView.OnSortingDataChanged", 0x015a7ff0)
dump_with_strings("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0)
dump_with_strings("StreamedTable_closures_after_0x015f33eb", 0x015f33f0, 0x2c0)
dump_with_strings("PropertyRegistration_J1Ct_0x00462600", 0x00462600, 0x350)
