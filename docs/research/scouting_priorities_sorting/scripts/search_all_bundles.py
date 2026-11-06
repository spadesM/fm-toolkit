import struct, sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

# Let's check all bundles in aa_dir that contain StreamedTable or ScoutPriorities or Priorities
for bpath in sorted(aa_dir.glob("ui-*.bundle")):
    try:
        raw = unpack_unityfs_bundle(bpath)
    except Exception as e:
        continue
    for kw in [b"ScoutPriorities", b"Priorities", b"SpecificallyScouted"]:
        if kw in raw:
            print(f"Bundle {bpath.name} contains {kw.decode()}")
