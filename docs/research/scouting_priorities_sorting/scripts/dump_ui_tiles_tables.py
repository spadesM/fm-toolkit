import struct, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean
from check_refs_and_grid import walk_tree

raw, trees, objs = parse_bundle_clean("ui-tiles_assets_all.bundle")
target_objs = [1371, 2298, 2559, 2942, 3412, 3429, 3668, 4250, 5007, 5083]

for i, pid, abs_off, bsize, tid in objs:
    if i in target_objs:
        cid, nodes = trees[tid]
        ln = struct.unpack_from("<I", raw, abs_off + 28)[0]
        name = raw[abs_off + 32 : abs_off + 32 + ln].decode("utf-8", errors="replace")
        chunk = raw[abs_off : abs_off + bsize]
        print(f"\n==================== Obj {i}: {name} (sz={bsize}) ====================")
        # Find all ASCII strings >= 4 chars
        strs = re.findall(rb"[A-Za-z0-9_\-\.]{4,}", chunk)
        uniq = []
        for s in strs:
            sd = s.decode("ascii", errors="ignore")
            if sd not in uniq and not sd.startswith("unity-"):
                uniq.append(sd)
        print("Strings:", uniq[:80])
        # Also parse StreamedTable if present!
        for st_node in [n for n in nodes if "StreamedTable" in n[2] or "StreamedListView" in n[2]]:
            print("Has node:", st_node)
