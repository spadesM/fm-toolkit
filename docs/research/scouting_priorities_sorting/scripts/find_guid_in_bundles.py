import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root

aa = root / "fm_Data" / "StreamingAssets" / "aa"
for p in aa.rglob("*"):
    if p.is_file() and p.suffix in (".json", ".bin", ".txt", ".xml"):
        print(p, p.stat().st_size)
