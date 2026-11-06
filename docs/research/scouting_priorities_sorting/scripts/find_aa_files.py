import os, sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root

aa_dir = root / "fm_Data/StreamingAssets/aa"
for dirpath, dirnames, filenames in os.walk(aa_dir):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        if not fn.endswith(".bundle") and not fn.endswith(".json") and not fn.endswith(".bin"):
            print("Other file:", p)
        if "catalog" in fn.lower() or "table" in fn.lower() or "visualscript" in fn.lower() or "function" in fn.lower() or "context" in fn.lower():
            print("Match file:", p)
