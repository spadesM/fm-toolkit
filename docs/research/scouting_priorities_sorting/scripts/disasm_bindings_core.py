import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import dump_with_strings
from check_deep_sorting import rva_to_method_name

for rva in sorted(rva_to_method_name):
    if 0x015f1000 <= rva <= 0x015f2000 or 0x015a4000 <= rva <= 0x015a4900:
        print(f"0x{rva:08x}: {rva_to_method_name[rva]}")

dump_with_strings("Bindings.GetNthProperty (0x014c1450)", 0x014c1450, 0x250)
dump_with_strings("Bindings.Bind (0x014bee30)", 0x014bee30, 0x350)
dump_with_strings("Bindings.Unbind (0x014c63d0)", 0x014c63d0, 0x250)
dump_with_strings("Bindings.TryOpenChannel (0x014c5820)", 0x014c5820, 0x300)
dump_with_strings("Func_015f14d0", 0x015f14d0, 0x250)
