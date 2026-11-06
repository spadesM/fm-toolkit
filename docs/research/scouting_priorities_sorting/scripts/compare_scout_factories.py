import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi in (92, 207, 232, 31):
    _, pid, abs_off, bsize, tid = objs_f[oi]
    _, nodes = trees_f[tid]
    chunk = raw_f[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n=== Factory Obj {oi} ({val.get('common_427')}) pid={pid} ===")
    print("  m_parameters:", val.get("m_parameters"))
    print("  m_emitIndexBinding:", val.get("m_emitIndexBinding"))
    print("  m_contextMenuBindingPath:", val.get("m_contextMenuBindingPath"))
    rows = val.get("m_rowData", [])
    print(f"  m_rowData ({len(rows)}):")
    for r in rows[:15]:
        print(f"    id={r.get('m_id'):25s} sort={r.get('m_sortBinding', {}).get('m_path')!r:65s} plugin={r.get('m_sortBindingPlugin')} asc={r.get('m_sortAscending')} valBinds={[(vb.get('from'), vb.get('to', {}).get('m_path'), vb.get('type', {}).get('id')) for vb in r.get('m_valueBindings', [])]}")
