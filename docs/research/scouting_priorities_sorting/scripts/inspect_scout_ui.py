import re
import struct
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
raw = unpack_unityfs_bundle(aa / "ui-recruitment_assets_all.bundle")

for label, pos in [
    ("ScoutPrioritiesBlock", 2350192),
    ("ScoutPrioritiesBlock-Small", 2608944),
    ("ShortlistMainBlock", 1406944),
]:
    print(f"=== {label} at {pos} ===")
    chunk = raw[pos : pos + 10000]
    st_pos = chunk.find(b"StreamedTable/UxmlSerializedData")
    print(f"StreamedTable/UxmlSerializedData relative offset: {st_pos}")
    if st_pos != -1:
        sub = chunk[st_pos : st_pos + 2000]
        for m in re.finditer(rb"[ -~]{2,}", sub):
            s = m.group(0).decode("ascii", errors="replace")
            print(f"  +{m.start():4d}: {s}")
        print("  HEX DUMP of StreamedTable/UxmlSerializedData (first 1200 bytes):")
        for off in range(0, min(1200, len(sub)), 32):
            h = sub[off:off+32].hex(" ")
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in sub[off:off+32])
            print(f"  {off:04x}: {h:<95} | {asc}")
