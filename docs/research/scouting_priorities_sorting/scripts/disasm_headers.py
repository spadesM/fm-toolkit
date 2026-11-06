from dump_headers_fast import dump_fast

targets = [
    ("StreamedListView..ctor_part2", 0x015ac200, 0x015acd10),
    ("StreamedTable.CreateHeader", 0x015e8f00, 0x015e90b0),
    ("StreamedTable.BindHeader", 0x015e6230, 0x015e6ca0),
    ("StreamedTable.BindHeaders", 0x015e6ca0, 0x015e6d70),
    ("StreamedTable.RecreateHeaders", 0x015eecb0, 0x015eed80),
]

for name, start, end in targets:
    dump_fast(name, start, end)
