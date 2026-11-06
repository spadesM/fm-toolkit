import struct, sys

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\prop_reg_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

print("=== Dump PropertyRegistration.Initialise around 0x00468800..0x00469200 ===")
dump_func_details("PropertyRegistration.Initialise_SpecificallyScouted", 0x00468800, 0xA00)

out_file.close()
