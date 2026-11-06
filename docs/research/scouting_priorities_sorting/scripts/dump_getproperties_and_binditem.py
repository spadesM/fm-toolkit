import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING check_deep_sorting ===")
for name, rva in [
    ("Bindings.GetProperties", 0x014c1a60),
    ("Func_00e030e0", 0x00e030e0),
    ("StreamedListView.SetSortingBinding_str", 0x015a9ae0),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedTable.OnBindItem", 0x015eb760),
    ("StreamedTable.OnMakeItem", 0x015ecc60),
    ("StreamedTable..ctor", 0x015f1930),
]:
    end = rva_to_end.get(rva, rva + 0x500)
    dump_func_details(name, rva, end - rva)
