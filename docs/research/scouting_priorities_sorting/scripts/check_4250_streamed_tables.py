import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean
from check_deep_sorting import root

cat = (root / "fm_Data" / "StreamingAssets" / "aa" / "catalog.bin").read_bytes()
for g in ("cd932659918436549aa73c273c17c719", "bd30edffabc96284cbfee63884ed3d7f", "ae1aa49648bd53c4682048ed437c045a", "43432bcfcddd0c54eba5fdbf83fe9203", "ee120f575ef93104b89d885705c3e93a"):
    pos = cat.find(g.encode("ascii"))
    if pos != -1:
        chunk = cat[pos - 80 : pos + 160]
        print(f"GUID {g}:", "".join(chr(b) if 32 <= b < 127 else "." for b in chunk))

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

raw, trees, objs = parse_bundle_clean("ui-tiles_assets_all.bundle")
for i, pid, abs_off, bsize, tid in objs:
    if i in (4250, 5083, 1371):
        chunk = raw[abs_off : abs_off + bsize]
        # Find all rid entries in ManagedReferencesRegistry
        # Each entry starts with 8-byte rid, then class string "StreamedTable/UxmlSerializedData", ns "SI.Bindable", asm "SI.Bindable"
        pat = b"StreamedTable/UxmlSerializedData"
        pos = 0
        entries = []
        while True:
            idx = chunk.find(pat, pos)
            if idx == -1:
                break
            rid = struct.unpack_from("<q", chunk, idx - 12)[0]
            # data starts after class (4+32=36), ns (4+11+1=16), asm (4+11+1=16) -> idx + 32 + 32 = idx + 64
            data_start = idx + 64
            entries.append((rid, data_start))
            pos = idx + 1
        # Wait: find where the next rid entry starts!
        # Let's scan for all (rid, class_len, ns_len, asm_len) in ManagedReferencesRegistry
        reg_pos = chunk.find(b"\x02\x00\x00\x00", len(chunk) // 2)
        for st_idx, (rid, dstart) in enumerate(entries):
            # Find end of this entry by looking for the next rid (e.g. rid+1 or rid+2 or -2)
            dend = None
            for next_rid in range(rid + 1, rid + 10):
                p = chunk.find(struct.pack("<q", next_rid), dstart)
                if p != -1 and p - dstart < 4000:
                    dend = p
                    break
            if dend is None:
                p = chunk.find(struct.pack("<q", -2), dstart)
                if p != -1:
                    dend = p
            if dend:
                dbytes = chunk[dstart:dend]
                tail = dbytes[-64:]
                bvals = {bool_names[k]: tail[k] for k in range(7)}
                fvals = {st_field_names[k]: tail[7 + k] for k in range(57)}
                print(f"\nObj {i} StreamedTable #{st_idx} (rid={rid}, len={len(dbytes)}):")
                print("  Bools:", {k: v for k, v in bvals.items() if v != 0})
                print("  Set Flags (val not in (0,2)):", {k: v for k, v in fvals.items() if v not in (0, 2)})
