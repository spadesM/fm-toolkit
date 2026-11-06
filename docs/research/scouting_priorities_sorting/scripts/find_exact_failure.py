import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, rva_to_method_name, dump_func_details, root
)
from list_recruitment_objs import parse_bundle_clean

# Question A: List all non-inlineStyle objects in ui-recruitment_assets_all.bundle by reading m_Name directly from abs_off
raw, trees, objs = parse_bundle_clean("ui-recruitment_assets_all.bundle")
print("=== Question A: All non-inlineStyle objects in ui-recruitment_assets_all.bundle ===")
for i, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    ln = struct.unpack_from("<I", raw, abs_off)[0]
    if 0 < ln < 200:
        name = raw[abs_off + 4 : abs_off + 4 + ln].decode("utf-8", errors="replace")
        if name != "inlineStyle":
            has_st = b"StreamedTable" in raw[abs_off : abs_off + bsize]
            print(f"  Obj {i:4d} (cls={cid}, pid={pid}, sz={bsize}): {name} {'[HAS StreamedTable]' if has_st else ''}")

# Question B: Dump Bindings.Bind (0x014bee30), Bindings.MakeKey (0x014c2040), Bindings.SetInternal (0x014c3770)
print("\n=== Question B: Bindings.Bind, Bindings.MakeKey, Bindings.SetInternal ===")
dump_func_details("Bindings.Bind", 0x014bee30, 0x350)
dump_func_details("Bindings.MakeKey", 0x014c2040, 0x250)
dump_func_details("Bindings.SetInternal", 0x014c3770, 0x350)

# Question C: List all methods of VirtualisedList and check Reorderable
print("\n=== Question C: VirtualisedList methods ===")
for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if "VirtualisedList." in name or "Reorderable" in name:
            print(f"  0x{rva:08x}: {name}")
