import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

targets = [
    ("Header.AddManipulator..Header.ctor", 0x015df450, 0x015dfea0),
    ("Bindings_sub_014d0b50", 0x014d0b50, 0x014d1000),
]

for name, s, e in targets:
    dhf.dump_fast(name, s, e)
