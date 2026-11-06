import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import resolve_metadata_usage, get_type_name, get_mstr, meta, hdr
import struct

usages = [
    (6, 209012),
    (1, 29016),
    (1, 57139),
    (1, 57140),
    (1, 57035),
    (1, 37208),
    (1, 23672),
    (1, 23676),
    (1, 56117),
    (1, 29376),
    (1, 38755),
    (6, 189930),
    (6, 189942),
    (6, 188300),
    (6, 208869),
    (6, 208724),
    (1, 53626),
    (6, 208814),
    (1, 34769),
    (6, 90535),
    (6, 90477),
]

for tag, idx in usages:
    print(f"MetaUsage(tag={tag}, idx={idx}) -> {resolve_metadata_usage(tag, idx)}")
