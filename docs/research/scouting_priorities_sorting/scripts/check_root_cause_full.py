import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

bool_names = [
    "DefaultSelectFirstElement",
    "AllowColumnReordering",
    "AllowColumnResizing",
    "ResizeColumnWidthsToFit",
    "ShowFooter",
    "DisableSorting",
    "DisableRowContextMenu"
]
st_field_names = [
    "TableConfig", "BackupTableConfig", "StyleSheetOverride", "Filter", "Columns", "TableRules",
    "OrderedColumns", "OrderedColumnsOutput", "SortedColumn", "DefaultSelectedColumn", "SecondaryFocusColumn",
    "ViewSelection", "OutputSingleSelectedData", "OutputSelectedDataList", "HiddenContextMenuItemBindings",
    "RequiredOptionalColumnBindings", "ColumnFormatArgsBindings", "RowClickedEvent", "SpaceBarEvent",
    "EnterKeyEvent", "BackSpaceKeyEvent", "AddEvents", "RemoveEvents", "DragEvents", "RowEnabledBoolean",
    "RowHighlightedBoolean", "AdditionalClassesQuery", "ColumnVisibilityConditionalList", "ContextMenuScope",
    "HeaderOverrideHeight", "MaximumColumns", "RowHeightMultiplier", "FillBottomEmptyRowsMaxHeight",
    "FillBottomEmptyRowsMinNumber", "FillBottomEmptyRowsTotalRows", "TableType", "InitFunction",
    "ColumnGapGroupID", "CustomAutomatorType", "SharedPersistenceID", "Identifier", "RowClassName",
    "CellClassName", "HeaderRowClassName", "HeaderCellClassName", "AddCellID", "DragCellID", "RemoveCellID",
    "MigrateAddEvent", "MigrateRemoveEvent", "DefaultSelectFirstElement", "AllowColumnReordering",
    "AllowColumnResizing", "ResizeColumnWidthsToFit", "ShowFooter", "DisableSorting", "DisableRowContextMenu"
]

print(f"Total bool_names={len(bool_names)}, st_field_names={len(st_field_names)}, sum={len(bool_names)+len(st_field_names)}")
# Wait: 7 + 57 = 64 bytes (0x40 bytes)! Exact multiple of 4!
for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    tail = dbytes[-64:]
    bvals = {bool_names[i]: tail[i] for i in range(7)}
    fvals = {st_field_names[i]: tail[7 + i] for i in range(57)}
    print(f"\n=== Obj {oi} ({name}) ===")
    print("  Bools:", {k: v for k, v in bvals.items() if v != 0})
    print("  Set Flags (val != 0 and val != 2):", {k: v for k, v in fvals.items() if v not in (0, 2)})
    print("  All non-zero Flags:", {k: v for k, v in fvals.items() if v != 0})
