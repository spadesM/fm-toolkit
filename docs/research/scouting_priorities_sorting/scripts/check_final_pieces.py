from disasm_more import dump_func_details
import struct

print("=== Dump SetSorting<T> (0x00abdcc0, 750) ===")
dump_func_details("SetSorting<T>", 0x00abdcc0, 750)

print("\n=== Dump StreamedTable.TrySetColumnsAndSort (0x015f0040, 1200) ===")
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 1200)

print("\n=== Dump StreamedTable.UpdateStreamedTableView (0x015f1650, 400) ===")
dump_func_details("StreamedTable.UpdateStreamedTableView", 0x015f1650, 400)

print("\n=== Dump Bindings.GetNthProperty (0x014c1450, 300) ===")
dump_func_details("Bindings.GetNthProperty", 0x014c1450, 300)

print("\n=== Dump Bindings.SetAlias (0x014c3050, 400) ===")
dump_func_details("Bindings.SetAlias", 0x014c3050, 400)

