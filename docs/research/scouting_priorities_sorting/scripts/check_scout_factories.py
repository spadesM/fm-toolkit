import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from list_all_factories import factories

for f in factories:
    if any(k in f['name'].lower() for k in ['scout', 'priorit', 'shortlist', 'personsearch']):
        print(f"=== {f['name']} (path_id={f['path_id']}, params={f['params']}) ===")
        for r in f['rows']:
            print(f"  id={r['id']!r:25s} sort={r['sort']!r:55s} asc={r['asc']} hdr={r['hdr']!r} vbinds={r['vbinds']}")
