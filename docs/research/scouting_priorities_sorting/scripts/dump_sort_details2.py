import sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

targets = [
    ("SpecificallyScoutedPersonReference_GetProperty", 0x00697200, 0x00697500),
    ("StreamedListView_600_to_1230", 0x015a4c00, 0x015a5600),
]

for name, s, e in targets:
    dump_fast(name, s, e)
