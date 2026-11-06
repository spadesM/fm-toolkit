import sys, struct, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from parse_recruitment_objs import raw, objs

# Let's print all objects in ui-recruitment_assets_all.bundle!
print(f"Total objects in ui-recruitment_assets_all.bundle: {len(objs)}")
for oi, path_id, abs_off, byte_size, type_id, name in objs:
    if name:
        print(f"  Obj {oi:3d}: {name:55s} (start=0x{abs_off:06x}, size={byte_size:6d}, type={type_id})")
