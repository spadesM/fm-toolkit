import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import dump_with_strings, resolve_data_rva
from check_deep_sorting import pe, image_base, off_to_va, va_to_off

# 1. Search all occurrences of the 7 property IDs of J1Ct across the entire PE
prop_vals = [
    (0x706c7972, "plyr"),
    (0x644d7861, "axMd"),
    (0x63594545, "EEYc"),
    (0x75446333, "3cDu"),
    (0x71754c76, "vLuq"),
    (0x73714e20, "_Nqs"),
    (0x6e475773, "sWGn"),
]
print("=== 1. Searching 7 Property IDs of J1Ct in PE ===")
for val, name in prop_vals:
    for endian, elabel in [("<I", "LE"), (">I", "BE")]:
        pat = struct.pack(endian, val)
        pos = 0
        hits = []
        while True:
            idx = pe.find(pat, pos)
            if idx == -1:
                break
            rva = off_to_va(idx) - image_base
            hits.append(f"0x{rva:08x}")
            pos = idx + 1
        if hits:
            print(f"  {name} (0x{val:08x} {elabel}): {', '.join(hits[:15])}")

# 2. Dump SpecificallyScoutedPersonReference methods from steps/4188/output.txt
# Let's check RVAs around 0x00696ef0
dump_with_strings("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0, 0x80)
dump_with_strings("SpecificallyScoutedPersonReference.GetPropertyInternal", 0x00696f70, 0x250)

# 3. Dump full Bindings.GetNthProperty (0x014c1450, size 0x220)
dump_with_strings("Bindings.GetNthProperty", 0x014c1450, 0x220)

# 4. Dump SetupRow (0x015aa320, size 0x260) with string literals
dump_with_strings("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x260)

# 5. Dump BindSortPathNextDepth (0x015a4850, size 0x1e0) with string literals
dump_with_strings("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x1e0)

# 6. Dump ProcessSortingDataChanged (0x015a8cb0, size 0x200) with string literals
dump_with_strings("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x200)
