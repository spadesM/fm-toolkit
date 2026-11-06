import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from parse_recruitment_objs import raw, objs

for oi, path_id, abs_off, byte_size, type_id, name in objs:
    if path_id == 7661162286614362349 or "RecruitmentScoutPriorities" in name:
        print(f"Found Obj {oi}: name={name!r} path_id={path_id} off=0x{abs_off:x} size={byte_size} type={type_id}")
        chunk = raw[abs_off : abs_off + byte_size]
        for line_off in range(0, len(chunk), 16):
            part = chunk[line_off : line_off + 16]
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in part)
            print(f"  +0x{line_off:04x}: {part.hex(' '):47s}  {ascii_str}")
