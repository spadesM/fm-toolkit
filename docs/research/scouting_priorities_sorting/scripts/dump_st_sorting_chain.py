import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

funcs = [
    ("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500),
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360),
    ("StreamedListView.set_Reorderable", 0x015ad4f0),
    ("StreamedListView.SetList", 0x015a9880),
    ("StreamedListView.SetSortingBinding_1", 0x015a9a80),
    ("StreamedListView.SetSortingBinding_2", 0x015a9ae0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
    ("StreamedTable.SetSorting_1", 0x015efc40),
    ("StreamedTable.SetSorting_2", 0x015efce0),
    ("StreamedTable.OnHeaderClicked", 0x015ec910),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
]

for name, rva in funcs:
    dump_func_details(name, rva)
