import struct, sys, os
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root
from inspect_vta_refs_and_props import walk_tree

# Check catalog.bin for the GUIDs
cat_path = root / "fm_Data/StreamingAssets/aa/catalog.bin"
cat_bytes = cat_path.read_bytes()
for guid in (
    "f93b92def36a8474fa5798233a6a3fb8",
    "446475dd53423864183c52075b8f0e32",
    "07913d3a50d1722459665dca2bf524a3",
    "f45d19f7c2614ae4782f06ccd001fbb1",
    "399c0aa9357f67847b91ba2fe4756083",
    "13a1f18bd93e860488c2cb84abb1168c",
    "c1a44f7eaa1698a43ab7664b7ce350da",
):
    # Search both ascii and utf-16le in catalog.bin
    for enc in ("ascii", "utf-16le"):
        b = guid.encode(enc)
        pos = cat_bytes.find(b)
        if pos != -1:
            print(f"Found {guid} ({enc}) in catalog.bin at 0x{pos:x}")
            # print surrounding printable text
            chunk = cat_bytes[max(0, pos-200):min(len(cat_bytes), pos+200)]
            if enc == "utf-16le":
                print("  Context:", chunk.decode("utf-16le", errors="ignore"))
            else:
                print("  Context:", "".join(chr(c) if 32 <= c < 127 else "." for c in chunk))
