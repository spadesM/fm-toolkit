import os, sys, glob, struct
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree

# Search all bundles for PathID 7661163991088543981 or "RecruitmentScoutPrioritiesBlock"
for bpath in sorted(glob.glob(os.path.join(aa_dir, "*.bundle"))):
    bname = os.path.basename(bpath)
    with open(bpath, "rb") as f:
        data = f.read()
    if b"RecruitmentScoutPrioritiesBlock" in data or b"ScoutPrioritiesBlock" in data:
        print(f"Found in raw bundle: {bname}")

# Also parse all ui-* bundles for RecruitmentScoutPrioritiesBlock
for bpath in sorted(glob.glob(os.path.join(aa_dir, "ui-*.bundle"))):
    bname = os.path.basename(bpath)
    try:
        raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    except Exception:
        continue
    if b"RecruitmentScoutPrioritiesBlock" in raw or b"ScoutPrioritiesBlock" in raw:
        print(f"\n=== Decompressed match in {bname} ===")
        for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
            chunk = raw[abs_off : abs_off + bsize]
            if b"RecruitmentScoutPrioritiesBlock" in chunk or b"ScoutPrioritiesBlock" in chunk or pid == 7661163991088543981:
                tname, nodes = trees[tid]
                top_c = [i for i, n in enumerate(nodes) if n[0] == 1]
                p = abs_off
                props = {}
                for c in top_c:
                    cname = nodes[c][3]
                    try:
                        p_next, val = walk_tree(nodes, raw, p, c)
                        props[cname] = val
                        p = p_next
                    except Exception:
                        break
                print(f"  Obj {oi} (PathID={pid}, Type={tname}): {props}")
