import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes('ui-tableviews_assets_all.bundle')
# all table views: print name + columns with sortingDisabled; summary of how many views disable sorting
stats = []
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_v):
    try:
        _, nodes = trees_v[tid]
        _, val = walk_tree(nodes, raw_v[abs_off: abs_off + bsize], 0, 0)
    except Exception:
        continue
    if not isinstance(val, dict) or 'm_tableView' not in val:
        continue
    cfg = val['m_tableView'].get('m_tableConfig', [])
    dis = [c['m_columnID'] for c in cfg if c['m_columnMetadata']['m_sortingDisabled']]
    stats.append((val.get('common_427'), len(cfg), dis))
    if oi in (766, 791):
        print(f"=== Obj {oi} {val.get('common_427')} abs_off={abs_off:#x} ===")
        for c in cfg:
            md = c['m_columnMetadata']
            print(f"   {c['m_columnID']:22s} required={md['m_required']} sortingDisabled={md['m_sortingDisabled']}")
print("\n=== Views having ANY sortingDisabled column ===")
for n, cnt, dis in stats:
    if dis:
        print(f"  {n}: {len(dis)}/{cnt} -> {dis}")
print(f"total views: {len(stats)}")
