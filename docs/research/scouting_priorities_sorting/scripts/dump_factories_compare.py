import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
    if not (0 <= tid < len(trees)):
        continue
    _, nodes = trees[tid]
    chunk = raw[abs_off : abs_off + bsize]
    if bsize < 36:
        continue
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 32 + ln <= len(chunk) else ""
    if "Person" in name or "Player" in name:
        print(f"Found factory Obj {oi}: {name!r} (bsize={bsize}, tid={tid})")
        try:
            _, val = walk_tree(nodes, chunk, 0, 0)
            print("  m_parameters:", val.get('m_parameters'))
            rows = val.get('m_rowData', [])
            print(f"  m_rowData count: {len(rows)}")
            for r in rows[:25]:
                col = r.get('common_436', r.get('m_columnID', ''))
                sb = r.get('m_sortBinding', {}).get('m_path', '')
                plug = r.get('m_sortBindingPlugin', 0)
                print(f"    col={col!r:28s} sortBind={sb!r:60s} plugin={plug}")
        except Exception as e:
            print(f"  walk_tree error: {e}")
