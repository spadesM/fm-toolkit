import struct, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from list_recruitment_objs import parse_bundle_clean

raw, trees, objs = parse_bundle_clean("ui-tiles_assets_all.bundle")
for i, pid, abs_off, bsize, tid in objs:
    if i in (4250, 5083, 1371):
        chunk = raw[abs_off : abs_off + bsize]
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        print(f"\n==================== Obj {i}: {name} (sz={bsize}) ====================")
        strs = re.findall(rb"[A-Za-z0-9_\-\.]{4,}", chunk)
        uniq = []
        for s in strs:
            sd = s.decode("ascii", errors="ignore")
            if sd not in uniq and not sd.startswith("unity-"):
                uniq.append(sd)
        print("All Strings:", uniq)
        # Find all occurrences of "StreamedTable\x00" in ManagedReferencesRegistry
        pos = 0
        while True:
            idx = chunk.find(b"StreamedTable", pos)
            if idx == -1:
                break
            print(f"  Found 'StreamedTable' at +0x{idx:x}: context={chunk[idx-20:idx+60]}")
            pos = idx + 1
