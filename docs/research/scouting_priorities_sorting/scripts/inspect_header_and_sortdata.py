import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name, get_mstr, methods_off, types_off, types_sz, images_off, images_sz, modules, dump_func_details
from annotate_sorting_usym import dump_annotated, literals

# 1. Search literals for "SpecificallyScoutedPlayers" or "ScoutPriorities"
for idx, s in enumerate(literals):
    if any(k in s.lower() for k in ("scoutpriorit", "specificallyscouted", "itemmoved", "drag-column")):
        print(f"Literal[{idx}] = {s!r}")

# 2. List all Header.* and SortData.* methods
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(n.startswith(p) for p in ("Header.", "SortData.", "SortingData")):
            sz = rva_to_end.get(rva, rva + 64) - rva
            print(f"0x{rva:08x} (sz={sz:4d}): {n}")

# 3. Dump key methods
for name, rva in [
    ("StreamedListView.get_ReceivedAllSortingData", 0x015acd40),
    ("StreamedListView.UpdateEnabledState", 0x015aab80),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("SortData.HasReceived", 0x015a4040),
    ("Header..ctor", 0x015dfab0),
    ("Header.Bind", 0x015df4f0),
    ("StreamedTable.UpdateSortColum", 0x015f1380),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedListView.RefreshInternal", 0x015a9060),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
