import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm9.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast

targets = [
    ("get_BindableFlags_00292620", 0x00292620),
    ("AutogenBindings_002ae590", 0x002ae590),
    ("StreamedTable..ctor_015f1930", 0x015f1930),
    ("StreamedTable.OnAttachToPanel_015eb750", 0x015eb750),
    ("StreamedTable.BindToDataInternal_015e6d70", 0x015e6d70),
    ("StreamedTable.OnFactoryAssetLoaded_015ec640", 0x015ec640),
    ("StreamedTable.OnViewSet_015ee7a0", 0x015ee7a0),
    ("StreamedTable.UpdateStreamedTableView_015f1650", 0x015f1650),
    ("StreamedTable.CreateColumnsFromTableView_015e8350", 0x015e8350),
    ("StreamedTable.CreateColumnsFromTableViewCollection_015e82c0", 0x015e82c0),
    ("StreamedTable.CanPopulateTable_015e7640", 0x015e7640),
    ("StreamedTable.CanBuild_015e7580", 0x015e7580),
    ("StreamedTable.SetSorting_015efc40", 0x015efc40),
    ("StreamedTable.UpdatePersistedColumnSortingData_015f1290", 0x015f1290),
    ("StreamedTable.EntryForColumn_015e9450", 0x015e9450),
    ("StreamedTable.UpdateSortColum_015f1380", 0x015f1380),
    ("StreamedTable.TryFindSortedColumn_015eff70", 0x015eff70),
    ("StreamedTable.MakeDefaultSelectedColumnHeader_015eb000", 0x015eb000),
    ("StreamedTable.<.ctor>b__206_0_015f0a70", 0x015f0a70),
    ("StreamedTable.<.ctor>b__206_1_015f0b30", 0x015f0b30),
    ("StreamedTable.<.ctor>b__206_2_015f0bf0", 0x015f0bf0),
    ("StreamedTable.OnBindItem_015eb760", 0x015eb760),
    ("StreamedTable.<OnBindItem>g__SetBindings|221_0_015f0580", 0x015f0580),
    ("StreamedListView.CanBuild_015a50b0", 0x015a50b0),
]

for name, rva in targets:
    end_rva = rva_to_end.get(rva, rva + 0x100)
    dump_fast(name, rva, end_rva)

out_file.close()
print("Done!", file=sys.__stdout__)
