import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_vf_and_tf import load_bundle, parse_obj
from check_refs_and_grid import walk_tree

print("=== 1. Inspect ui-tableviews_assets_all.bundle ===")
raw_tv, trees_tv, objs_tv = load_bundle("ui-tableviews_assets_all.bundle")
for i in range(len(objs_tv)):
    try:
        d = parse_obj(raw_tv, trees_tv, objs_tv, i)
        name = str(d.get("common_427", ""))
        if any(w in name for w in ("ScoutPriorities", "TeamReportPriorities", "ShortlistTableViewCollection", "PersonSearchTableViewCollection")):
            print(f"\nTV Obj[{i}] ({name}, pid={d['_pid']}):")
            for k, v in d.items():
                print(f"  {k}: {v!r}")
    except Exception as e:
        pass

print("\n=== 2. Inspect InitialiseStreamedTable* in ui-visualfunctions_assets_all.bundle ===")
raw_vf, trees_vf, objs_vf = load_bundle("ui-visualfunctions_assets_all.bundle")
for i in range(len(objs_vf)):
    oi, pid, abs_off, bsize, tid = objs_vf[i]
    _, nodes = trees_vf[tid]
    try:
        d = parse_obj(raw_vf, trees_vf, objs_vf, i)
        name = str(d.get("common_427", ""))
        if "InitialiseStreamedTable" in name:
            print(f"\nVF Obj[{i}] ({name}, pid={pid}, bsize={bsize}):")
            # Let's also see where references start and print strings/fields in raw bytes of this object
            obj_bytes = raw_vf[abs_off : abs_off + bsize]
            # Extract ASCII strings of length >= 3 from obj_bytes
            import re
            strs = [m.group(0).decode("ascii", errors="replace") for m in re.finditer(rb"[\x20-\x7e]{3,}", obj_bytes)]
            print("  ASCII strings in object:", strs)
    except Exception as e:
        pass
