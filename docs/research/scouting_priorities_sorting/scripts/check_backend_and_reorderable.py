import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# 1. Dump PropertyRegistration for ScoutPlayerPrioritiesReference (0x00468300..0x00468700)
dump_func_details("PropertyRegistration_ScoutPlayerPriorities", 0x00468300, 0x380)

# 2. Dump PropertyRegistration for SpecificallyScoutedPersonReference (0x0046b000..0x0046b500)
dump_func_details("PropertyRegistration_SpecificallyScoutedPerson", 0x0046b000, 0x480)

# 3. Dump VirtualisedList.UpdateSortValues (0x015b7dd0), StreamedListView.ApplySorting (0x015a4260), StreamedTable.ApplySorting (0x015e5940)
dump_func_details("VirtualisedList.UpdateSortValues", 0x015b7dd0)
dump_func_details("StreamedListView.ApplySorting", 0x015a4260)
dump_func_details("StreamedTable.ApplySorting", 0x015e5940)
