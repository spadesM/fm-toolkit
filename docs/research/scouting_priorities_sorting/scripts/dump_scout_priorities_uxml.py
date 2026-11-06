import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from parse_recruitment_objs import raw, objs

# Let's inspect all strings inside Obj 177 (RecruitmentScoutPrioritiesCard), Obj 229 (ScoutPrioritiesBlock), Obj 263 (ScoutPrioritiesBlock-Small), Obj 144 (RecruitmentTeamReportPrioritiesCard), Obj 360 (RecruitmentTeamReportPrioritiesTableBlock)
for target_oi in (177, 229, 263, 144, 360):
    oi, path_id, abs_off, byte_size, type_id, name = objs[target_oi]
    print(f"\n==================== Obj {oi}: {name} (off=0x{abs_off:x}, size={byte_size}) ====================")
    chunk = raw[abs_off : abs_off + byte_size]
    # Find all length-prefixed strings (aligned to 4 bytes)
    for p in range(0, len(chunk) - 4, 4):
        slen = struct.unpack_from("<I", chunk, p)[0]
        if 1 <= slen <= 120 and p + 4 + slen <= len(chunk):
            s = chunk[p + 4 : p + 4 + slen]
            # check padding zeros
            pad = (4 - (slen % 4)) % 4
            if p + 4 + slen + pad <= len(chunk) and chunk[p + 4 + slen : p + 4 + slen + pad] == b"\x00" * pad:
                if all(32 <= b < 127 for b in s):
                    print(f"  +0x{p:04x}: {s.decode('ascii')!r}")
