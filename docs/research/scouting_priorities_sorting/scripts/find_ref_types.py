import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, dump_func_details, rva_to_method_name, va_to_off, off_to_va, image_base,
    types_off, types_sz, methods_off, get_mstr, hdr
)

# Find all types in FM.UI that end with Reference and have Scout or Recruitment or Priority or Shortlist in their name!
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    ns = get_mstr(tu[1])
    if "Reference" in tname and any(w in tname.lower() for w in ("scout", "priorit", "recruit", "shortlist", "assign")):
        print(f"Type #{ti}: {ns}.{tname}")
