import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf

for name, rva in [
    ("rylp", 0x0046ede5),
    ("axMd", 0x0046b097),
    ("EEYc", 0x0046cb53),
    ("3cDu", 0x00468d8f),
    ("vLuq", 0x00468ca3),
    ("Nqs", 0x00468c2d),
    ("sWGn", 0x00468bb7),
]:
    dhf.dump_fast(f"Prop_{name}", rva - 0x20, rva + 0x70)
