import sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

targets = [
    ("StreamedListView_1232_to_705", 0x015a9c80, 0x015aad00),
    ("StreamedListView_2072_2078", 0x015a5b00, 0x015a6000),
    ("StreamedListView_882_to_1201", 0x015a4200, 0x015a4900),
]

for name, s, e in targets:
    dump_fast(name, s, e)
