import sys
sys.stdout.reconfigure(encoding="utf-8")
from annotate_sorting_usym import dump_annotated

targets = [
    ("StreamedTable.OnMakeItem", 0x015ecc60),
    ("StreamedTable.OnBindItem", 0x015eb760),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0", 0x015f0580),
    ("StreamedTable.OnRebindItem", 0x015ed7d0),
    ("StreamedTable.OnStartReorder", 0x015ee350),
    ("StreamedTable.OnReorder", 0x015edbe0),
    ("StreamedTable.OnEndReorder", 0x015ec410),
    ("StreamedListView..ctor", 0x015aba20),
    ("StreamedTable..ctor", 0x015eff00),
]

for name, rva in targets:
    dump_annotated(name, rva)

from check_deep_sorting import rva_to_end, rva_to_method_name, dump_func_details
# Find closest function before 0x696f54
cands = [r for r in rva_to_end if r <= 0x696f54]
if cands:
    fn = max(cands)
    print(f"Closest function before 0x696f54: {rva_to_method_name.get(fn, hex(fn))} at 0x{fn:08x}..0x{rva_to_end[fn]:08x}")
dump_func_details("Around 0x696e80..0x697500", 0x696e80, 0x680)

