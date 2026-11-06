import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import (
    pe, meta, types_off, types_sz, methods_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated

sorted_rvas = sorted(rva_to_method_name.keys())
def find_func(rva):
    idx = bisect.bisect_right(sorted_rvas, rva) - 1
    if idx >= 0:
        frva = sorted_rvas[idx]
        return frva, rva_to_method_name[frva]
    return 0, []

for call_rva in (0x015a8e9a, 0x015a9cd0):
    frva, names = find_func(call_rva)
    print(f"Caller 0x{call_rva:08x} is in 0x{frva:08x} (+0x{call_rva-frva:03x}): {names}")
    dump_annotated(str(names), frva)
    dump_func_details(str(names), frva)

for name, rva in [
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedListView.SetDirty", 0x015a9780),
    ("StreamedListView.UpdateEnabledState", 0x015aab80),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
