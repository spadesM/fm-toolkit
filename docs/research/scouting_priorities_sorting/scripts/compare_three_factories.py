import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")

pid_to_obj = {pid: (i, abs_off, bsize, tid) for i, pid, abs_off, bsize, tid in objs}

def dump_factory(oi):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    cid, nodes = trees[tid]
    _, val = walk_tree(nodes, chunk, 0)
    print(f"\n================ Obj {oi} (PathID={pid}): {val.get('m_Name')} ================")
    for k, v in val.items():
        if k == "m_rowData":
            print(f"  m_rowData ({len(v)} items):")
            for rd in v[:12]:
                print(f"    {rd}")
        else:
            print(f"  {k}: {v}")
    for bf in val.get("m_baseFactory", []):
        bpid = bf.get("m_PathID")
        if bpid in pid_to_obj:
            boi = pid_to_obj[bpid][0]
            print(f"  -> BaseFactory Obj {boi} (PathID={bpid})")

dump_factory(92)
for i, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 36:
        ln = struct.unpack_from("<I", chunk, 28)[0]
        if 0 < ln < 200:
            name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
            if name in ("PersonTableFactory", "PlayerTableFactory", "RecruitmentPlayerTableFactory", "PlayerSearchTableFactory", "ScoutingCentrePersonTableFactory"):
                dump_factory(i)
