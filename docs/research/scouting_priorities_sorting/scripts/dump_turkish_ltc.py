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

for pat in (b"turkish\x04\x00\x00\x00.ltc", b"english\x04\x00\x00\x00.ltc"):
    pos = 0
    while True:
        p = dir_raw.find(pat, pos)
        if p == -1:
            break
        ext_end = p + len(pat)
        rel_off, comp_sz, uncomp_sz = struct.unpack_from("<QQQ", dir_raw, ext_end)
        # Note: in the second subfolder of languages.fmf, is rel_off relative to the first or second block?
        print(f"\nFound {pat[:7].decode()} at dir+{p}: rel_off=0x{rel_off:x}, comp_sz={comp_sz}, uncomp_sz={uncomp_sz}")
        pos = p + 1
