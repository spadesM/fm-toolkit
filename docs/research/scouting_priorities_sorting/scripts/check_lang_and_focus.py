import struct, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean

raw, trees, objs = parse_bundle_clean("ui-recruitment_assets_all.bundle")
target_indices = [177, 229, 263, 301, 360, 363, 367]
for i, pid, abs_off, bsize, tid in objs:
    if i in target_indices:
        chunk = raw[abs_off : abs_off + bsize]
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        # Find all ASCII strings >= 4 chars in chunk
        strs = re.findall(rb"[A-Za-z0-9_\-\.]{4,}", chunk)
        uniq = []
        for s in strs:
            sd = s.decode("ascii", errors="ignore")
            if any(k in sd for k in ("Table", "List", "Sort", "Priorit", "Focus", "Scout", "Player", "Bind", "View", "Template", "Block", "Card", "Streamed")):
                if sd not in uniq:
                    uniq.append(sd)
        print(f"\n=== Obj {i} ({name}, sz={bsize}) ===")
        print("  Strings:", uniq[:60])
