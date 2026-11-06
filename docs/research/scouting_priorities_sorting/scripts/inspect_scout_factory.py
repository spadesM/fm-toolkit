import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

def dump_bundle_objs(bundle_name, filter_names):
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bundle_name)
    for oi, pid, abs_off, bsize, tid in objs:
        if bsize < 32 or tid >= len(trees):
            continue
        chunk = raw[abs_off : abs_off + bsize]
        ln = struct.unpack_from("<I", chunk, 28)[0]
        if not (0 < ln < 200):
            continue
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        if any(fn.lower() in name.lower() for fn in filter_names):
            class_id, nodes = trees[tid]
            print(f"\n=== {bundle_name} Obj {oi} (pid={pid}, class={class_id}): {name} ===")
            print("  tree top nodes:", [(i, n[2], n[3]) for i, n in enumerate(nodes) if n[0] == 1])
            try:
                _, val = walk_tree(nodes, chunk, 0, 0)
                if isinstance(val, dict):
                    for k, v in val.items():
                        if isinstance(v, list):
                            print(f"  {k}: list of {len(v)}")
                            for idx, item in enumerate(v[:50]):
                                print(f"    [{idx}] {item}")
                        else:
                            print(f"  {k}: {v}")
            except Exception as e:
                print(f"  walk_tree error: {e}")

if __name__ == "__main__":
    dump_bundle_objs("ui-tablefactories_assets_all.bundle", ["SpecificallyScouted", "PersonSearch", "Scout"])
    dump_bundle_objs("ui-tableviews_assets_all.bundle", ["ScoutPriorities", "SpecificallyScouted"])
    dump_bundle_objs("ui-recruitment_assets_all.bundle", ["ScoutPriorities", "SpecificallyScouted"])
