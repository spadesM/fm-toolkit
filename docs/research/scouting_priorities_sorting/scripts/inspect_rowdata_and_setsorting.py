import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# 1. Check types 6130..6142 (around TableTemplate = 6138) and 5780..5791 (around StreamedListView = 5791)
for ti in list(range(6130, 6142)) + [5951]:
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    f_start, f_cnt = tu[8], tu[17] & 0xFFFF
    fnames = [get_mstr(struct.unpack_from("<3i", meta, fields_off + fi * 12)[0]) for fi in range(f_start, f_start + f_cnt)]
    print(f"Type {ti}: {tname} -> fields={fnames}")

# 2. Dump Header..ctor (0x015dfab0), Header.Bind (0x015df4f0), StreamedTable.UpdateSortColum (0x015f1380), StreamedListView.SetList (0x015a9880)
for name, rva in [
    ("Header..ctor", 0x015dfab0),
    ("Header.Bind", 0x015df4f0),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
    ("StreamedListView.SetList", 0x015a9880),
]:
    dump_func_details(name, rva)
