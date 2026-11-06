from dump_headers_fast import dump_fast

targets = [
    ("StreamedTable_015e5850", 0x015e5850, 0x015e58c0),
    ("StreamedTable_015e8f30", 0x015e8f30, 0x015e9050),
    ("StreamedTable.MakeColumnHeader", 0x015eac00, 0x015eb020),
    ("StreamedTable.MakeDefaultSelectedColumnHeader", 0x015eb020, 0x015eb200),
    ("StreamedTable_015ec2e0", 0x015ec2e0, 0x015ec410),
    ("StreamedTable_015ed280", 0x015ed280, 0x015ed400),
    ("StreamedTable.UpdateSortShortcut_015f14d0", 0x015f14d0, 0x015f1650),
    ("StreamedTableView_016214f0", 0x016214f0, 0x01621650),
    ("Bindings_014d13f0", 0x014d13f0, 0x014d1700),
]

for name, s, e in targets:
    dump_fast(name, s, e)
