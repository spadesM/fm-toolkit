from check_deep_sorting import dump_func_details
from annotate_sorting_usym import dump_annotated

# 1. Disassemble StreamedTableView.CreateFromTableConfig and RebuildLookup
for name, rva in [
    ("StreamedTableView.CreateFromTableConfig", 0x01621320),
    ("StreamedTableView.RebuildLookup", 0x01621a50),
    ("StreamedTableViewSettingsCollection.<RebuildLookup>g__AddTablesViewsInList|23_0", 0x01620de0),
    ("StreamedTableViewSettingsCollection_GetLastSelectedValue", 0x0152b4a0),
]:
    dump_annotated(name, rva)
    dump_func_details(name, rva)
