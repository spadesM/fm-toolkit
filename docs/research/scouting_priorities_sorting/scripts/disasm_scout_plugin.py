import struct
import sys
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# First, let's check all types in SI.Bindable.dll or FM.GamePlugin.dll around RVA 0x0111c000..0x01123000 and RecordSerialisation (around 0x01650920)
for rva in sorted(rva_to_method_name.keys()):
    if 0x0111b000 <= rva <= 0x01125000 or 0x0164f000 <= rva <= 0x01655000:
        print(f"0x{rva:08x}: {rva_to_method_name[rva]}")

# Let's check if capstone is available for game_plugin.dll disassembly
try:
    import capstone
    print("Capstone available!")
except ImportError:
    print("Capstone not available")
