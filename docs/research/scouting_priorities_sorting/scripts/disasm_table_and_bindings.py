from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name
from annotate_sorting_usym import dump_annotated, resolve_rip_va

targets = [
    ("Bindings.Bind", 0x014bee30),
    ("Bindings.Unbind", 0x014c63d0),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.OnMakeItem", 0x015ecc60),
    ("StreamedTable.SetSorting", 0x015efce0),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
]

for name, rva in targets:
    dump_annotated(name, rva)
