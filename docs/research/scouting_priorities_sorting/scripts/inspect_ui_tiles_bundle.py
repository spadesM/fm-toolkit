import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean
from check_refs_and_grid import walk_tree

raw, trees, objs = parse_bundle_clean("ui-tiles_assets_all.bundle")
for i, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 32:
        ln = struct.unpack_from("<I", raw, abs_off + 28)[0]
        if 0 < ln < 200:
            name = raw[abs_off + 32 : abs_off + 32 + ln].decode("utf-8", errors="replace")
            if any(k in name for k in ("Scout", "Priorit", "RecruitmentFocus")):
                chunk = raw[abs_off : abs_off + bsize]
                has_st = b"StreamedTable" in chunk
                has_tt = b"TableTemplate" in chunk
                print(f"ui-tiles Obj {i:4d} (pid={pid:20d}, sz={bsize:6d}): {name:50s} ST={has_st} TT={has_tt}")
