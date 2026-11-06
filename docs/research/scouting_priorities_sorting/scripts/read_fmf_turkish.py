import struct, sys, io, re, zstandard
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root

fmf_path = root / "data" / "game_simulation" / "languages.fmf"
with open(fmf_path, "rb") as f:
    hdr = f.read(26)
    dir_off = struct.unpack_from("<Q", hdr, 9)[0]
    f.seek(dir_off)
    dir_comp = f.read()

dctx = zstandard.ZstdDecompressor()
idx = dir_comp.find(b"\x28\xb5\x2f\xfd")
with dctx.stream_reader(io.BytesIO(dir_comp[idx:])) as r:
    dir_raw = r.read()
print(f"Decompressed dir from +{idx}: {len(dir_raw)} bytes")
for m in re.finditer(rb"(?:[ -~]\x00){3,}", dir_raw):
    s = m.group().decode("utf-16-le", errors="replace")
    e = m.end()
    print(f"  {s!r} at dir+{m.start()} (after={dir_raw[e:e+28].hex(' ')})")
for m in re.finditer(rb"[ -~]{4,}", dir_raw):
    print(f"  ascii {m.group().decode('ascii')!r} at dir+{m.start()} (after={dir_raw[m.end():m.end()+28].hex(' ')})")
