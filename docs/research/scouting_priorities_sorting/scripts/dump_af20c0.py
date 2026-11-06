import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING ===")
for name, rva in [
    ("Func_00af20c0", 0x00af20c0),
    ("Func_00abdcc0", 0x00abdcc0),
    ("StreamedListView.UpdateSortColum", 0x015f1380),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580),
]:
    end = rva_to_end.get(rva, rva + 0x300)
    dump_func_details(name, rva, end - rva)
