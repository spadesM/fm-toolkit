import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm3.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast

funcs = [
    ("StreamedListView.SetSorting<T>", 0x00abdcc0),
    ("Header.<>c__DisplayClass36_0.<.ctor>b__0", 0x015f2ea0),
    ("Header..ctor", 0x015dfab0),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.SetSorting", 0x015efce0),
    ("SortData.ReceivedAllDataForRow", 0x015a4040),
    ("SortComparer.Compare(x,y)", 0x015a3c60),
    ("SortComparer.Compare_obj", 0x015a3d30),
    ("Bindings.GetNthProperty", 0x014c1450),
    ("Bindings.BindProperty", 0x014bee30),
    ("Bindings.TryGetPropertyValue", 0x014c63d0),
    ("Bindings.CreateScope", 0x014bf980),
    ("Bindings.RegisterScope_or_1940", 0x014c3050),
    ("Bindings.Set_1919", 0x014c5740),
    ("SpecificallyScoutedPersonReference.get_Player", 0x00696ef0),
    ("SpecificallyScoutedPersonReference.get_Scout", 0x00697020),
    ("SpecificallyScoutedPersonReference.get_Assignments", 0x00697130),
    ("SpecificallyScoutedPersonReference.get_Knowledge", 0x00697250),
]

for name, rva in funcs:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dump_fast(name, rva, end_rva)

out_file.close()
