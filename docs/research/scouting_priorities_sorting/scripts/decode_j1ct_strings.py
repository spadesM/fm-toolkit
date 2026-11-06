import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, meta, image_base, off_to_va, va_to_off

# In IL2CPP, string literals like _stringLiteral1234 are in .data and initialized from metadata string literals!
# Even simpler: we can compute the hash function at 0x002ae590!
# Wait: let's disassemble 0x002ae590 first to see what it does, AND check the call before 0x002ae590 in PropertyRegistration.Initialise!
from check_deep_sorting import dump_func_details
dump_func_details("0x002ae590", 0x002ae590, 0x60)
dump_func_details("0x002a5ec0 (called at +0x009 of decode_property_hashes)", 0x002a5ec0, 0x100)
dump_func_details("0x00c57b60", 0x00c57b60, 0x100)
dump_func_details("0x014c0fb0 (Bindings.GetHandler)", 0x014c0fb0, 0x200)
dump_func_details("0x014c5350 (Bindings.SetTargetData)", 0x014c5350, 0x350)
