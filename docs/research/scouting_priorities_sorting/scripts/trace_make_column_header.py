import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details, pe, meta, hdr, image_base, va_to_off, rva_to_method_name, get_mstr, types_off, methods_off
from annotate_sorting_usym import dump_annotated

dump_func_details("StreamedTable.MakeColumnHeader", 0x015eac30, 973)
dump_func_details("Bindings.GetProperties", 0x014c1a60)
dump_annotated("Bindings.GetProperties", 0x014c1a60)
dump_func_details("Func_0x00e030e0", 0x00e030e0, 0x100)
dump_func_details("Func_0x010e4ed0", 0x010e4ed0, 0x100)
dump_func_details("Func_0x010b5f90", 0x010b5f90, 0x100)
