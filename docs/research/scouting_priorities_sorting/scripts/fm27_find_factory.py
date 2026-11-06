import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
sys.stdout.reconfigure(encoding='utf-8')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

cols = ['inf', 'drag-column', 'name', 'age', 'nation', 'club', 'scouted-best-position-and-role', 'recommendation-grade-only',
        'assigned-staff', 'progress-remaining', 'assigment-length', 'transfer-value', 'index']
raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes('ui-tablefactories_assets_all.bundle')
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_f):
    try:
        _, nodes = trees_f[tid]
        _, val = walk_tree(nodes, raw_f[abs_off: abs_off + bsize], 0, 0)
    except Exception:
        continue
    if not isinstance(val, dict) or 'm_rowData' not in val: continue
    ids = [r.get('m_id') for r in val['m_rowData']]
    if 'progress-remaining' in ids or 'assigment-length' in ids:
        name = val.get('m_Name') or val.get('common_427')
        print(f"=== Factory Obj {oi} {name} pid={pid} abs_off={abs_off:#x} rows={len(ids)} ===")
        print("  params:", [(p.get('name'), p.get('type')) for p in val.get('m_parameters', [])])
        for r in val['m_rowData']:
            if r.get('m_id') in cols:
                vbs = [(vb.get('from'), vb.get('to', {}).get('m_path')) for vb in r.get('m_valueBindings', [])]
                print(f"  {r['m_id']:32s} sort={r.get('m_sortBinding')} plugin={r.get('m_sortBindingPlugin')} asc={r.get('m_sortAscending')} vb={vbs}")
