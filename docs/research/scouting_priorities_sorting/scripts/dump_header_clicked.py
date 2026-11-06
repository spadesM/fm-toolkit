import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_end

print("=== DONE IMPORTING ===")
for name, rva in [
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.SetSorting_1", 0x015efc40),
    ("StreamedTable.SetSorting_2", 0x015efce0),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70),
]:
    end = rva_to_end.get(rva, rva + 0x300)
    dump_func_details(name, rva, end - rva)
