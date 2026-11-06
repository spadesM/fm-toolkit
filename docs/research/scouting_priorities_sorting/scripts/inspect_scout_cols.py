import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes('ui-tableviews_assets_all.bundle')
cols = []
for oi in (236, 766, 791):
    _, pid, abs_off, bsize, tid = objs_v[oi]
    _, nodes = trees_v[tid]
    _, val = walk_tree(nodes, raw_v[abs_off : abs_off + bsize], 0, 0)
    print(f'=== TableView Obj {oi} (pid={pid}) ===')
    for k, v in val.items():
        if k != 'm_tableConfig':
            print(f'  {k}: {v}')
        else:
            for c in v:
                cid = c.get('m_columnID')
                if cid and cid not in cols: cols.append(cid)
                print('   ', c)

raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes('ui-tablefactories_assets_all.bundle')
for oi in (92, 31, 14):
    _, pid, abs_off, bsize, tid = objs_f[oi]
    _, nodes = trees_f[tid]
    _, val = walk_tree(nodes, raw_f[abs_off : abs_off + bsize], 0, 0)
    print(f'=== Factory Obj {oi} ({val.get("m_Name") or val.get("common_427")}) ===')
    print('  m_parameters:', val.get('m_parameters'))
    print('  m_parentFactories:', val.get('m_parentFactories'))
    for r in val.get('m_rowData', []):
        if r.get('m_id') in cols or oi == 92:
            vbs = [(vb.get('from'), vb.get('to', {}).get('m_path')) for vb in r.get('m_valueBindings', [])]
            print(f"  {r.get('m_id'):28s}: sortBinding={r.get('m_sortBinding')}, sortField={r.get('m_sortField')}, sortAsc={r.get('m_sortAscending')}, disableSort={r.get('m_disableSorting')}, valBinds={vbs}")
