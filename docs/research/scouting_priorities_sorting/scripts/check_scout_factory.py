import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")

target_cols = {'inf', 'player-nationality', 'age', 'club-division', 'position', 'recommendation', 'staff', 'assignment-type', 'value'}

for oi in (92, 31):
    _, pid, abs_off, bsize, tid = objs[oi]
    _, nodes = trees[tid]
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    p = abs_off
    props = {}
    for c in top_children:
        cname = nodes[c][3]
        p_next, val = walk_tree(nodes, raw, p, c)
        props[cname] = val
        p = p_next
    print(f"\n==================== ui-tablefactories Obj {oi} ({props.get('common_427')}) ====================")
    print("  m_parameters:", props.get("m_parameters"))
    print("  m_emitIndexBinding:", props.get("m_emitIndexBinding"))
    print("  m_contextMenuBindingPath:", props.get("m_contextMenuBindingPath"))
    row_data = props.get("m_rowData", [])
    print(f"  m_rowData: len={len(row_data)}")
    for rd in row_data:
        if oi == 92 or rd.get("m_columnID") in target_cols:
            print("   ", rd)
