from dump_headers_fast import dump_fast

funcs = [
    ("StreamedTable.OnHeaderClicked (StreamedTable.cs:962)", 0x015ec910, 0x015ecc60),
    ("StreamedTable.SetSorting_1 (StreamedTable.cs:2040)", 0x015efc40, 0x015efce0),
    ("StreamedTable.SetSorting_2 (StreamedTable.cs:2047)", 0x015efce0, 0x015f0040),
    ("StreamedTable.TrySetColumnsAndSort (StreamedTable.cs:1118)", 0x015f0040, 0x015f0340),
    ("StreamedTable.MakeColumnHeader (StreamedTable.cs:1395)", 0x015eac30, 0x015eb080),
    ("ScoutPlayerPrioritiesReference.GetInstance", 0x0067d310, 0x0067d360),
    ("SpecificallyScoutedPersonReference.GetInstance", 0x00696f70, 0x00696f80),
]

for name, rva, end_rva in funcs:
    print("================================================================================")
    dump_fast(name, rva, end_rva)
