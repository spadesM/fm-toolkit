import struct, sys, bisect
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, root, image_base, va_to_off, rva_to_end, rva_to_method_name, sections
from annotate_sorting_usym import dump_annotated

# 1. Check catalog.bin for InitFunction and HeaderCellAsset GUIDs
cat = (root / "fm_Data" / "StreamingAssets" / "aa" / "catalog.bin").read_bytes()
guids = [
    ("ScoutPriorities InitFunction", "f93b92def36a8474fa5798233a6a3fb8"),
    ("Shortlist InitFunction", "446475dd53423864183c52075b8f0e32"),
    ("HeaderCellAsset", "f45d19f7c2614ae4782f06ccd001fbb1"),
    ("ScoutPrioritiesTableViewCollection", "13a1f18bd93e860488c2cb84abb1168c"),
    ("ScoutPrioritiesTable-Small", "c1a44f7eaa1698a43ab7664b7ce350da"),
]
print("=== 1. Catalog.bin lookup for GUIDs ===")
for label, g in guids:
    for enc in ("ascii", "utf-16-le"):
        pos = cat.find(g.encode(enc))
        if pos != -1:
            chunk = cat[max(0, pos - 160) : min(len(cat), pos + 200)]
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print(f"  {label} ({g}, {enc}) @ {pos}:\n    {printable}")

# 2. Check all StreamedTable methods with "Init" in their name
print("\n=== 2. StreamedTable Init methods ===")
sorted_rvas = sorted(rva_to_method_name.keys())
def find_enclosing_method(rva):
    idx = bisect.bisect_right(sorted_rvas, rva) - 1
    if idx >= 0:
        srva = sorted_rvas[idx]
        return f"{rva_to_method_name[srva][0]} (0x{srva:08x}+0x{rva-srva:x})"
    return "unknown"

init_rvas = []
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if ("StreamedTable." in n or "StreamedListView." in n) and ("Init" in n or "Header" in n or "Sort" in n):
            print(f"  0x{rva:08x}: {n}")
            if "Init" in n:
                init_rvas.append((n, rva))

for n, rva in init_rvas:
    dump_annotated(n, rva)

# 3. Also scan all StreamedTable methods for 0x940..0x958 to see what offsets around 0x940 are accessed!
print("\n=== 3. Offsets 0x930..0x960 accessed in StreamedTable ===")
for rva, names in sorted(rva_to_method_name.items()):
    if any("StreamedTable." in n for n in names):
        sz = rva_to_end.get(rva, rva + 256) - rva
        off = va_to_off(image_base + rva)
        code = pe[off : off + sz]
        for target_disp in range(0x930, 0x968, 8):
            pat = struct.pack("<I", target_disp)
            if pat in code:
                print(f"  +0x{target_disp:03x} referenced in {names[0]} (0x{rva:08x})")
