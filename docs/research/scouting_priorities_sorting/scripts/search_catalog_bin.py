import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root

cat = (root / "fm_Data" / "StreamingAssets" / "aa" / "catalog.bin").read_bytes()
guids = [
    "cf0dd6dadc040da40bdc6ebb7938a1fe",
    "76c0db9d2a0cbb14c89cabd9751b52a0",
    "b7a2109802a2acc4f8df99455c8c5541",
    "aaf938fd5cc48884f92da232066336ee",
    "d42dfeb48822f814fba16c3fcec5ea75",
    "0ae390edaecad894dbd8abf49cf5d619",
    "c520af498a12fe542b72d72ffe51d29f",
    "457480f7b5730ee4eaacb86237ce6b3e",
]
for g in guids:
    pos = cat.find(g.encode("ascii"))
    chunk = cat[pos - 120 : pos + 160]
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"\nGUID {g} @ {pos}:")
    print(" ", printable)
