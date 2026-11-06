import struct, sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

keywords = [
    b"ScoutPriorities",
    b"SpecificallyScouted",
    b"399c0aa9357f67847b91ba2fe4756083", # SpecificallyScoutedPersonTableFactory GUID
    b"13a1f18bd93e860488c2cb84abb1168c", # ScoutPrioritiesTableViewCollection GUID
    b"c1a44f7eaa1698a43ab7664b7ce350da", # ScoutPrioritiesTableViewCollection-Small GUID
    b"99226", # translation key for Gözlemci Öncelikleri
]

for fn in sorted(os.listdir(aa_dir)):
    if not fn.endswith(".bundle") or "ui-" not in fn:
        continue
    p = aa_dir / fn
    try:
        raw = unpack_unityfs_bundle(p)
    except Exception:
        continue
    hits = []
    for kw in keywords:
        c = raw.count(kw)
        if c > 0:
            hits.append(f"{kw.decode('ascii')}:{c}")
    if hits:
        print(f"{fn}: {', '.join(hits)}")
