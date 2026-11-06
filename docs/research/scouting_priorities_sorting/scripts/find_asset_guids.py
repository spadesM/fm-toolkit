import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
import UnityPy

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

# Let's check catalog.bin for these GUIDs!
cat_path = aa_dir.parent / "catalog.bin"
if cat_path.exists():
    data = cat_path.read_bytes()
    for guid in ("f93b92def36a8474fa5798233a6a3fb8", "446475dd53423864183c52075b8f0e32", "f45d19f7c2614ae4782f06ccd001fbb1"):
        for enc in ("ascii", "utf-16-le"):
            b = guid.encode(enc)
            pos = data.find(b)
            if pos >= 0:
                snippet = data[max(0, pos-120):min(len(data), pos+200)]
                print(f"Found {guid} ({enc}) at {pos}: {snippet}")

# Also let's check ui-tableviews, ui-tablefactories, ui-widgets, ui-datacollections, ui-functions, etc.
for bpath in sorted(aa_dir.glob("ui-*.bundle")):
    if any(k in bpath.name for k in ("function", "table", "widget", "recruitment", "common", "core", "shared", "header", "cell")):
        print("Candidate bundle:", bpath.name)
