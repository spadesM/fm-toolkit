import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean
from check_refs_and_grid import walk_tree

raw, trees, objs = parse_bundle_clean("ui-recruitment_assets_all.bundle")
pid_to_name = {}
for i, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 32:
        ln = struct.unpack_from("<I", raw, abs_off + 28)[0]
        if 0 < ln < 200:
            name = raw[abs_off + 32 : abs_off + 32 + ln].decode("utf-8", errors="replace")
            pid_to_name[pid] = (i, name)

for i, pid, abs_off, bsize, tid in objs:
    if i == 176:
        cid, nodes = trees[tid]
        _, val = walk_tree(nodes, raw, abs_off, 0)
        for k, v in val.items():
            if isinstance(v, list) and len(v) > 10:
                print(f"Key {k} (len={len(v)}), first={v[0]}")
                for item in v:
                    if isinstance(item, dict) and "common_778" in item:
                        apid = item["common_778"].get("asset", {}).get("m_PathID")
                        if apid in pid_to_name:
                            oi, oname = pid_to_name[apid]
                            print(f"  {item.get('common_155')} -> Obj {oi:4d} ({oname})")
