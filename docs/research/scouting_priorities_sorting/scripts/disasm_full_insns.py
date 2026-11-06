from check_deep_sorting import dump_func_details
from annotate_sorting_usym import dump_annotated

for name, rva in [
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.SetSorting", 0x015efce0),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("Bindings.GetProperties", 0x014c1a60),
    ("Bindings.Bind (path)", 0x014bee30),
    ("Bindings.Bind (node)", 0x014beef0),
    ("Bindings.Unbind", 0x014c63d0),
]:
    dump_func_details(name, rva)
