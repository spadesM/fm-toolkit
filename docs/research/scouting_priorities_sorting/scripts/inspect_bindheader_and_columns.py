import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

dump_fast("StreamedTable.BindHeader (0x015e6230)", 0x015e6230, 0x015e6d70)
dump_fast("StreamedTable.BindToDataInternal (0x015e6d70)", 0x015e6d70, 0x015e7573)
dump_fast("StreamedTable.MakeColumnHeader (0x015eac30)", 0x015eac30, 0x015eb000)
dump_fast("StreamedListView.StateChanged (0x015a9c80)", 0x015a9c80, 0x015a9ee0)
dump_fast("StreamedListView.OnSortBindingChanged (0x015a7ca0)", 0x015a7ca0, 0x015a7ff0)
dump_fast("StreamedListView.SortData.HasReceived (0x015a4040)", 0x015a4040, 0x015a4190)
dump_fast("StreamedListView.OnSortingDataChanged (0x015a7ff0)", 0x015a7ff0, 0x015a8200)

def load_named_obj(bundle_name, target_names):
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bundle_name)
    res = {}
    for oi, pid, abs_off, bsize, tid in objs:
        if bsize < 32 or tid >= len(trees):
            continue
        chunk = raw[abs_off : abs_off + bsize]
        ln = struct.unpack_from("<I", chunk, 28)[0]
        if not (0 < ln < 200):
            continue
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        if name in target_names:
            class_id, nodes = trees[tid]
            _, val = walk_tree(nodes, chunk, 0, 0)
            res[name] = (oi, pid, val)
    return res

tf = load_named_obj("ui-tablefactories_assets_all.bundle", {"SpecificallyScoutedPersonTableFactory", "PlayerTableFactory"})
tv = load_named_obj("ui-tableviews_assets_all.bundle", {"ScoutPrioritiesTable", "ScoutPrioritiesTable-Small", "ScoutPrioritiesTableViewCollection", "ScoutPrioritiesTableViewCollection-Small"})

print("\n" + "="*90)
print("SpecificallyScoutedPersonTableFactory COLUMNS:")
print("="*90)
ss_cols = {}
if "SpecificallyScoutedPersonTableFactory" in tf:
    _, _, val = tf["SpecificallyScoutedPersonTableFactory"]
    for idx, row in enumerate(val.get("m_rowData", [])):
        cid = row.get("m_columnID")
        sb = row.get("m_sortBinding")
        sbp = row.get("m_sortBindingPlugin")
        ss_cols[cid] = row
        print(f"  [{idx:02d}] col={cid:<32} sortBinding={sb!r:<35} plugin={sbp}")

for tv_name in ["ScoutPrioritiesTable", "ScoutPrioritiesTable-Small", "ScoutPrioritiesTableViewCollection", "ScoutPrioritiesTableViewCollection-Small"]:
    if tv_name in tv:
        oi, pid, val = tv[tv_name]
        print(f"\n=== {tv_name} (Obj {oi}, pid={pid}) ===")
        if "m_tableView" in val:
            for idx, c in enumerate(val["m_tableView"]):
                cid = c.get("m_columnID")
                md = c.get("m_columnMetadata", {})
                ov = c.get("m_columnMetadataOverride", {})
                f_row = ss_cols.get(cid, {})
                print(f"  [{idx:02d}] col={cid:<28} md.sortingDisabled={md.get('m_sortingDisabled')} ov.sortingDisabled={ov.get('m_sortingDisabled')} | factory.sortBinding={f_row.get('m_sortBinding')!r} plugin={f_row.get('m_sortBindingPlugin')}")
        else:
            print("  val:", val)
