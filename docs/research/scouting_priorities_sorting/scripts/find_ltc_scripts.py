import sys, struct, glob, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

# Let's check existing scripts in scratch that parsed turkish.ltc
scratch = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch"
for fn in os.listdir(scratch):
    if "ltc" in fn or "lang" in fn or "turk" in fn or "fmf" in fn:
        print("Found script:", fn)
