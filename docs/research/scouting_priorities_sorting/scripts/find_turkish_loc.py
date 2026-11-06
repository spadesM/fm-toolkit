import sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
print("Install dir:", root)
for p in root.rglob("*"):
    if p.is_file() and any(k in p.name.lower() for k in ("tur", "loc", "lang", "ltf")):
        print("Found:", p)
