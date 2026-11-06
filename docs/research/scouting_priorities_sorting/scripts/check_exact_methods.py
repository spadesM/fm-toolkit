import check_deep_sorting as cds

# Find exact RVAs for StreamedTable and StreamedListView methods
for rva, names in sorted(cds.rva_to_method_name.items()):
    for n in names:
        if n.startswith("StreamedTable.") or n.startswith("StreamedListView."):
            print(f"0x{rva:08x}: {n}")

cds.dump_func_details("Func_0x00292620", 0x00292620, 64)
cds.dump_func_details("Func_0x00a28ae0", 0x00a28ae0, 128)
cds.dump_func_details("StreamedTable_0x015ef750", 0x015ef750)
cds.dump_func_details("StreamedListView.SetList", 0x015a9880)
cds.dump_func_details("StreamedListView.SetNoSorting", 0x015a99d0)
cds.dump_func_details("StreamedListView.EndStateChange", 0x015a5350)
cds.dump_func_details("StreamedListView.Rebuild", 0x015a8eb0)
cds.dump_func_details("StreamedTable.ApplyPersistedSortingState", 0x015e58c0)
cds.dump_func_details("StreamedTable.GeneratePersistenceKeys", 0x015e9600)
