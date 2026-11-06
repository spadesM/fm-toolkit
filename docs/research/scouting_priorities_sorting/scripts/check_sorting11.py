import sys
from dump_headers_fast import dump_fast, get_usym_dict
from check_deep_sorting import rva_to_end, rva_to_method_name

with open("sorting_disasm11.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    targets = [
        ("Header..ctor", 0x015dfab0),
        ("Header.SetupClickHandler", 0x015df7e0),
        ("Header.Bind", 0x015df4f0),
        ("Header.OnBindingChanged", 0x015df600),
        ("Header.ResetSortingIcons", 0x015df720),
        ("Header.UpdateSortingIcons", 0x015df970),
        ("StreamedTable.BindHeader", 0x015e6230),
        ("StreamedTable.BindHeaders", 0x015e6ca0),
        ("StreamedTable.CreateHeader", 0x015e8f00),
        ("StreamedTable.MakeColumnHeader", 0x015eac30),
        ("StreamedTable.RecreateHeaders", 0x015eecb0),
        ("StreamedTable.CreateColumn", 0x015e7dc0),
        ("StreamedTable.CreateColumns", 0x015e83b0),
        ("StreamedTable.InitialiseColumns", 0x015ea870),
        ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
        ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
        ("StreamedTable.OnHeaderClicked", 0x015ec910),
        ("StreamedTable.OnSortColumn", 0x015ee250),
        ("StreamedTable.SetSorting_1", 0x015efc40),
        ("StreamedTable.SetSorting_2", 0x015efce0),
        ("StreamedTable.SetNoSorting", 0x015ef750),
        ("StreamedTable.UpdateSortColum", 0x015f1380),
        ("StreamedTable.UpdateSortShortcut", 0x015f14d0),
        ("StreamedTable.EnableSortShortcut", 0x015e93a0),
        ("StreamedTable.DisableSortShortcut", 0x015e9340),
        ("StreamedTable.TryFindSortedColumn", 0x015eff70),
        ("StreamedTable.SetList", 0x015ef610),
        ("StreamedTable.BindToDataInternal", 0x015e6d70),
        ("StreamedTable.RebuildInternal", 0x015ee9c0),
        ("StreamedTable.RefreshInternal", 0x015eed80),
        ("StreamedTable.OnStartReorder", 0x015ee350),
        ("StreamedTable.OnReorder", 0x015edbe0),
        ("StreamedTable.OnEndReorder", 0x015ec410),
        ("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0),
        ("StreamedListView.UxmlSerializedData.Deserialize", 0x015b0b50),
    ]

    for name, rva in targets:
        end_rva = rva_to_end.get(rva, rva + 0x400)
        dump_fast(name, rva, min(end_rva, rva + 0x1000))
