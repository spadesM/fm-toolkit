import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf
from check_deep_sorting import dump_func_details, rva_to_method_name, off_to_va

raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees_r["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    cname, nodes = trees_r[tid]
    node_names = [n[3] for n in nodes]
    if "m_VisualElementAssets" not in node_names and "common_452" not in node_names:
        continue
    chunk = raw_r[abs_off : abs_off + bsize]
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    if idx != -1:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        p = idx + 64
        st_val = {}
        for c in top_children:
            fn = st_nodes[c][3]
            try:
                p, val = walk_tree(st_nodes, chunk, p, c)
                st_val[fn] = val
            except Exception as e:
                break
        b_path = st_val.get("Binding", {}).get("m_path", "")
        sb_path = st_val.get("SortBinding", {}).get("m_path", "")
        reord = st_val.get("Reorderable", 0)
        dis_sort = st_val.get("DisableSorting", 0)
        drag_cell = st_val.get("DragCellID", "")
        drag_ev = st_val.get("DragEvents", "")
        tf = st_val.get("TableFactory", {}).get("m_AssetGUID", "")
        tv = st_val.get("TableViews", {}).get("m_AssetGUID", "")
        print(f"Obj {oi:3d} ({name:48s}): Binding='{b_path}' SortBinding='{sb_path}' Reord={reord} DisSort={dis_sort} DragCell='{drag_cell}' TF={tf[:8]} TV={tv[:8]}")

dump_func_details("sub_00abdcc0 (called by SetSortingBinding_2)", 0x00abdcc0)
dump_func_details("sub_00af20c0 (called by SetSortingBinding_2)", 0x00af20c0)
dump_func_details("StreamedListView.HasSorting", 0x015a5f20)
dump_func_details("StreamedListView.ApplySorting", 0x015a4260)
dump_func_details("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0)
dump_func_details("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320)
dump_func_details("StreamedListView.BindSortPathNextDepth", 0x015a4850)
