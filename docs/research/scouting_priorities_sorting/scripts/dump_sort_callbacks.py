import sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

targets = [
    ("UpdateSortingBinding", 0x015ab800, 0x015ab9b0),
    ("OnSortBindingChanged_to_OnSortingDataChanged", 0x015a7ca0, 0x015a8110),
    ("PostSortingDataChanged", 0x015a8610, 0x015a86c0),
    ("ProcessSortingDataChanged", 0x015a8cb0, 0x015a8eb0),
    ("HasSorting", 0x015a5f20, 0x015a6000),
]

for name, s, e in targets:
    dump_fast(name, s, e)
