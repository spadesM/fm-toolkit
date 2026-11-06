import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
sys.stdout.reconfigure(encoding='utf-8')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes('ui-tableviews_assets_all.bundle')
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_v):
    try:
        _, nodes = trees_v[tid]
        _, val = walk_tree(nodes, raw_v[abs_off: abs_off + bsize], 0, 0)
    except Exception:
        continue
    if not isinstance(val, dict): continue
    name = str(val.get('common_427'))
    if 'ScoutPriorit' not in name and 'SpecificallyScouted' not in name: continue
    print(f"=== Obj {oi} {name} pid={pid} abs_off={abs_off:#x} ===")
    if 'm_tableView' in val:
        for c in val['m_tableView'].get('m_tableConfig', []):
            md = c['m_columnMetadata']
            print(f"   {c['m_columnID']:22s} required={md['m_required']} sortingDisabled={md['m_sortingDisabled']}")
    else:
        print("  views:", [v.get('PropertyValue') for v in val.get('m_tableViewSettings', [])])

raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes('ui-tablefactories_assets_all.bundle')
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_f):
    try:
        _, nodes = trees_f[tid]
        _, val = walk_tree(nodes, raw_f[abs_off: abs_off + bsize], 0, 0)
    except Exception:
        continue
    if not isinstance(val, dict): continue
    name = str(val.get('m_Name') or val.get('common_427'))
    if 'SpecificallyScouted' not in name: continue
    print(f"=== Factory Obj {oi} {name} pid={pid} ===")
    for r in val.get('m_rowData', []):
        keys = {k: v for k, v in r.items() if k not in ('m_valueBindings', 'm_uxml', 'm_headerUxml')}
        short = {k: (v if len(str(v)) < 80 else str(v)[:80]) for k, v in keys.items()}
        print("  ", short)
