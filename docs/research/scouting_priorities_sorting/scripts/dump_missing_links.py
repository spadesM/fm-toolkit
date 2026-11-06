import sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

targets = [
    ("SetSorting_Generic_0x00abdcc0", 0x00abdcc0, 0x00abdf00),
    ("StreamedListView.DoSorting_0x015a5350", 0x015a5350, 0x015a5600),
    ("StreamedListView_0x015a5b90_to_0x015a6000", 0x015a5b90, 0x015a6000),
    ("StreamedListView.OnSortingDataChanged_0x015a7ff0", 0x015a7ff0, 0x015a8300),
    ("SpecificallyScoutedPersonReference_All", 0x00696ef0, 0x00697380),
    ("ScoutPlayerPrioritiesReference_All", 0x0067d270, 0x0067d660),
]

for name, s, e in targets:
    dump_fast(name, s, e)
