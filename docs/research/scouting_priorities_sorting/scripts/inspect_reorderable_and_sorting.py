import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, rva_to_end, rva_to_method_name, get_mstr, methods_off, types_off, dump_func_details
from annotate_sorting_usym import dump_annotated, resolve_rip_va

# Let's also resolve Il2CppType usage (tag=1 or tag=2) from metadata!
# In global-metadata.dat:
# hdr[36], hdr[37] = typeDefinitions or metadataUsageLists? Let's print hdr pairs and resolve Type index 32982
print("Header fields:")
for i in range(0, 64, 2):
    print(f"  hdr[{i:2d}] off={hdr[i]:8d} sz={hdr[i+1]:8d}")

targets = [
    ("StreamedListView.set_Reorderable", 0x015ad4f0),
    ("StreamedTable.get_DisableSorting", 0x015f2190),
    ("StreamedTable.set_DisableSorting", 0x015f2420),
    ("StreamedTable.get_IsDragCellActive", 0x015f2230),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedTable.SetSorting(1)", 0x015efc40),
    ("StreamedTable.SetSorting(2)", 0x015efce0),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedListView.ApplySorting", 0x015a4260),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
]

for name, rva in targets:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
