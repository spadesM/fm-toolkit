import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import rva_to_method_name, rva_to_end
from dump_headers_fast import dump_fast

print("=== Methods in 0x015a3ea0..0x015b2000 (StreamedListView) ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015a3ea0 <= rva <= 0x015b2000:
        end = rva_to_end.get(rva, rva)
        print(f"  0x{rva:08x}..0x{end:08x} (sz={end-rva:4d}): {rva_to_method_name[rva]}")

print("\n=== Methods in 0x015de900..0x015f5000 (StreamedTable) ===")
for rva in sorted(rva_to_method_name.keys()):
    if 0x015de900 <= rva <= 0x015f5000:
        end = rva_to_end.get(rva, rva)
        print(f"  0x{rva:08x}..0x{end:08x} (sz={end-rva:4d}): {rva_to_method_name[rva]}")

dump_fast("StreamedListView.OnSortingDataChanged (0x015a7ff0..0x015a8610)", 0x015a7ff0, 0x015a8610)
