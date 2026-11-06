import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean

raw, trees, objs = parse_bundle_clean("ui-tileslayouts_assets_all.bundle")
for i, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 32:
        ln = struct.unpack_from("<I", raw, abs_off + 28)[0]
        if 0 < ln < 200:
            name = raw[abs_off + 32 : abs_off + 32 + ln].decode("utf-8", errors="replace")
            if any(k in name for k in ("ScoutPriorit", "RecruitmentFocusTool")):
                print(f"ui-tileslayouts Obj {i:4d} (pid={pid}, sz={bsize}): {name}")
