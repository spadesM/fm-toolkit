import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import (
    pe, meta, hdr, str_off, str_sz, methods_off, methods_sz, types_off, types_sz,
    get_mstr, get_lit, image_base, va_to_off, get_usym_dict, resolve_rip, dump_fast
)

# 1. Dump the key StreamedTable / VirtualisedList / StreamedListView methods
targets = [
    ("VirtualisedList_set_Reorderable", 0x016abea0, 0x016abf80),
    ("StreamedTable_OnHeaderClicked", 0x015ec910, 0x015ecb70),
    ("StreamedTable_SetSorting_2_and_4", 0x015efc40, 0x015f0230),
    ("StreamedTable_MakeColumnHeader", 0x015eac30, 0x015eb000),
    ("StreamedTable_BindHeader", 0x015e6230, 0x015e6ca0),
    ("StreamedTable_CreateColumn", 0x015e7dc0, 0x015e83b0),
    ("StreamedTable_SetList", 0x015ef610, 0x015ef890),
    ("StreamedTable_CreateColumnsFromTableViewCollection", 0x015e8b20, 0x015e8e10),
    ("StreamedTable_CreateColumnsFromTableView", 0x015e87a0, 0x015e8b20),
    ("StreamedListView_UpdateSortingBinding", 0x015ab800, 0x015ab9b0),
]

for name, s, e in targets:
    dump_fast(name, s, e)
