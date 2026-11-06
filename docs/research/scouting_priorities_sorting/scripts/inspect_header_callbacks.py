import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from check_deep_sorting import (
    pe, meta, image_base, va_to_off, rva_to_end, rva_to_method_name,
    get_mstr, methods_off, types_off, images_off, images_sz, modules, dump_func_details
)
from annotate_sorting_usym import dump_annotated

dump_func_details("Header.<>c__DisplayClass36_0.<.ctor>b__0", 0x015f2ea0)
dump_annotated("Header.<>c__DisplayClass36_0.<.ctor>b__0", 0x015f2ea0)
dump_func_details("Header.SetupClickHandler", 0x015df7e0)
dump_annotated("Header.SetupClickHandler", 0x015df7e0)
dump_func_details("Header.Bind", 0x015df4f0)
dump_annotated("Header.Bind", 0x015df4f0)
dump_func_details("Header.OnBindingChanged", 0x015df600)
dump_annotated("Header.OnBindingChanged", 0x015df600)
dump_func_details("Header.UpdateSortingIcons", 0x015df970)
dump_annotated("Header.UpdateSortingIcons", 0x015df970)
dump_func_details("Header.ResetSortingIcons", 0x015df720)
dump_annotated("Header.ResetSortingIcons", 0x015df720)
dump_func_details("StreamedTable.<MakeColumnHeader>b__0", 0x0160bb80)
dump_annotated("StreamedTable.<MakeColumnHeader>b__0", 0x0160bb80)
dump_func_details("StreamedTable.SetSorting(col, asc)", 0x015efc40)
dump_annotated("StreamedTable.SetSorting(col, asc)", 0x015efc40)
dump_func_details("StreamedTable.TryFindSortedColumn", 0x015eff70)
dump_annotated("StreamedTable.TryFindSortedColumn", 0x015eff70)
