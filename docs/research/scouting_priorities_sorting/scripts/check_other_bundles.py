import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

for bname in ["ui-tiles_assets_all.bundle", "ui-panelids-uxml_assets_all.bundle", "ui-columns_assets_all.bundle"]:
    raw = unpack_unityfs_bundle(aa_dir / bname)
    print(f"=== {bname} (len={len(raw)}) ===")
    for kw in [b"ScoutPriorities", b"SpecificallyScouted"]:
        pos = 0
        while True:
            idx = raw.find(kw, pos)
            if idx < 0:
                break
            start = max(0, idx - 64)
            end = min(len(raw), idx + 128)
            import re
            strs = [m.group().decode("ascii", errors="replace") for m in re.finditer(rb"[ -~]{4,}", raw[start:end])]
            print(f"  {kw.decode()} at {idx} (0x{idx:x}): {strs}")
            pos = idx + 1
