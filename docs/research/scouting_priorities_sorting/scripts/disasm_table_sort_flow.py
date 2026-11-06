import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

# Find methods by name in cds.rva_to_method_name
targets = [
    "MakeColumnHeader",
    "OnSortColumn",
    "Sort",
    "StreamedTableHeader",
]

for b_rva, names in sorted(cds.rva_to_method_name.items()):
    if 0x01590000 <= b_rva <= 0x01630000:
        for n in names:
            if any(t in n for t in targets):
                e_rva = cds.rva_to_end.get(b_rva, b_rva + 0x100)
                print(f"0x{b_rva:08x}..0x{e_rva:08x}: {names}")

dhf.dump_fast("StreamedTable.cs:107 (0x015dfab0)", 0x015dfab0, cds.rva_to_end.get(0x015dfab0, 0x015dfe00))
dhf.dump_fast("StreamedTable.cs:1230 (0x015e58c0)", 0x015e58c0, cds.rva_to_end.get(0x015e58c0, 0x015e5c00))
dhf.dump_fast("StreamedTable.cs:2006 (0x015efc40)", 0x015efc40, cds.rva_to_end.get(0x015efc40, 0x015eff00))
dhf.dump_fast("StreamedListView.cs:705 (0x015aab80)", 0x015aab80, cds.rva_to_end.get(0x015aab80, 0x015aaf00))
