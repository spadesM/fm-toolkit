import sys, time
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
from fm26save.binary_decompiler import unpack_unityfs_bundle
d = use_fm27.FM27 / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
keys = [b"ScoutPriorities.SpecificallyScoutedPlayers", b"ScoutPrioritiesBlock", b"SpecificallyScoutedPersonTableFactory",
        b"ScoutPrioritiesTable", b"scoutpriorities", b"ScoutPriorities"]
t0 = time.time()
for f in sorted(d.glob("*.bundle")):
    try:
        raw = unpack_unityfs_bundle(f)
    except Exception as e:
        print("ERR", f.name, e); continue
    hits = [k.decode() for k in keys if k in raw]
    if hits:
        print(f.name, len(raw), hits, flush=True)
print("done", round(time.time() - t0, 1), "s")
