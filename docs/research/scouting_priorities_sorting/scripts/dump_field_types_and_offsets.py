import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, types_off, fields_off, get_mstr,
    va_to_off, off_to_va, image_base, dump_func_details
)

# Let's also disassemble OnHeaderClicked (full size), SetSorting (full size), and ProcessSortingDataChanged (0x015a8cb0)
dump_func_details("StreamedTable.OnHeaderClicked_FULL", 0x015ec910, 0x280)
dump_func_details("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x350)
dump_func_details("Bindings.GetProperties", 0x014c1a60, 0x200)
dump_func_details("Sub_00e030e0 (called in SetSorting)", 0x00e030e0, 0x100)
