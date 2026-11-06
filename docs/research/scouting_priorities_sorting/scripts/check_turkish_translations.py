import struct, zstandard, zlib
from check_deep_sorting import root

fmf_path = root / "data/game_simulation/languages.fmf"
with open(fmf_path, "rb") as f:
    hdr = f.read(64)
print("languages.fmf header:", hdr[:32], hdr[:32].hex(" "))

# Also search raw bytes of languages.fmf for UTF-8 / UTF-16 "Gözlemcilik"
raw = fmf_path.read_bytes()
for enc in ["utf-8", "utf-16-le"]:
    pat = "Gözlemcilik".encode(enc)
    idx = raw.find(pat)
    print(f"Search 'Gözlemcilik' ({enc}): idx={idx}")
