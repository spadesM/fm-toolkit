import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from parse_recruitment_objs import raw, objs

oi, path_id, abs_off, byte_size, type_id, name = objs[177]
chunk = raw[abs_off + 0x0ad0 : abs_off + 0x1560]
for line_off in range(0, len(chunk), 16):
    part = chunk[line_off : line_off + 16]
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in part)
    print(f"  +0x{0x0ad0 + line_off:04x}: {part.hex(' '):47s}  {ascii_str}")
