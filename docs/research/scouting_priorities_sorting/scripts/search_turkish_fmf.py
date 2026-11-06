import sys, os, struct, zstandard
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root
from list_recruitment_objs import parse_bundle_clean

fmf_path = root / "data" / "game_simulation" / "languages.fmf"
data = fmf_path.read_bytes()
print("languages.fmf size:", len(data), "header:", data[:64].hex(" "))

# Find zstd frames (0x28 0xb5 0x2f 0xfd) in languages.fmf
magic = b"\x28\xb5\x2f\xfd"
pos = 0
frames = []
while True:
    idx = data.find(magic, pos)
    if idx == -1:
        break
    frames.append(idx)
    pos = idx + 4
print(f"Found {len(frames)} zstd frames in languages.fmf: first 10 = {frames[:10]}")

# Check if "turkish" or "tur.ltf" or similar is in languages.fmf directory table (often at the end or after first frame)
dctx = zstandard.ZstdDecompressor()
for fi, foff in enumerate(frames):
    try:
        dec = dctx.decompress(data[foff:], max_output_size=50_000_000)
        if b"G\xc3\xb6zlemcilik" in dec or "Gözlemcilik".encode("utf-16-le") in dec or b"turkish" in dec.lower():
            print(f"  Frame {fi} at {foff}: decompressed {len(dec)} bytes, MATCH!")
            for pat_str in ("Gözlemcilik Öncelikleri", "Gözlemcilik", "Scout Priorities", "Scouting Priorities"):
                for enc in ("utf-8", "utf-16-le"):
                    p = dec.find(pat_str.encode(enc))
                    if p != -1:
                        print(f"    Found {pat_str!r} ({enc}) at {p}: context={dec[max(0,p-32):p+64]}")
    except Exception as e:
        pass
