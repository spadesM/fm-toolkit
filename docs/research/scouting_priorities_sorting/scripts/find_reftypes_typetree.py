import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from inspect_vta_refs_and_props import raw

# Let's search raw (the decompressed SerializedFile of ui-recruitment_assets_all.bundle) for "DisableSorting" and "FactoryAsset"!
for s in (b"DisableSorting\x00", b"FactoryAsset\x00", b"HeaderCellAsset\x00", b"ContextMenuData\x00", b"InitFunction\x00"):
    pos = 0
    while True:
        idx = raw.find(s, pos)
        if idx == -1:
            break
        print(f"Found {s!r} in raw at 0x{idx:x}")
        # Print surrounding strings in the string buffer
        chunk = raw[max(0, idx-200):min(len(raw), idx+400)]
        print("  Strings:", [x.decode('ascii', errors='replace') for x in chunk.split(b'\x00') if x])
        pos = idx + 1
