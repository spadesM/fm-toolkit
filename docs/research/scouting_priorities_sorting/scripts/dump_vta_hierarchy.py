import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

def dump_vta(target_oi, label):
    for oi, pid, abs_off, bsize, tid in objs:
        if oi != target_oi:
            continue
        chunk = raw[abs_off : abs_off + bsize]
        class_id, nodes = trees[tid]
        print(f"\n==================== {label} (Obj {oi}, pid={pid}, size={bsize}) ====================")
        pos = 0
        for i, n in enumerate(nodes):
            if n[0] == 1:
                fname = n[3]
                if fname == "references":
                    print("  [stopping before references at pos", pos, "of", len(chunk), "]")
                    break
                pos, fval = walk_tree(nodes, chunk, pos, i)
                if isinstance(fval, list) and fval:
                    print(f"  {fname} ({len(fval)}):")
                    for idx, item in enumerate(fval):
                        print(f"    [{idx}] {item}")
                elif fval:
                    print(f"  {fname}: {fval}")

dump_vta(177, "RecruitmentScoutPrioritiesCard")
dump_vta(229, "ScoutPrioritiesBlock")
dump_vta(263, "ScoutPrioritiesBlock-Small")
dump_vta(103, "RecruitmentPlayerRecommendationsCard")
dump_vta(360, "RecruitmentTeamReportPrioritiesTableBlock")
