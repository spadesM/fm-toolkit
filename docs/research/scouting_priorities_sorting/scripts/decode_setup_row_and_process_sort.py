import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# Let's dump Bindings.GetNthProperty, Bindings.Bind, Bindings.SetAlias, Bindings.Unbind, and SortData.HasReceived
for label, rva in [
    ("Bindings.GetNthProperty", 0x014c1450),
    ("Bindings.SetAlias", 0x014c3050),
    ("Bindings.Bind", 0x014bee30),
    ("Bindings.Unbind", 0x014c63d0),
    ("SortData.HasReceived", 0x015a4040),
    ("Helper_0x00e030e0", 0x00e030e0),
    ("Helper_0x00abdcc0", 0x00abdcc0),
]:
    dump_func_details(label, rva)
