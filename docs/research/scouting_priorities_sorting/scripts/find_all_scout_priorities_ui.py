import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
import UnityPy

root = resolve_fm_install_dir()
bundle_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

env = UnityPy.load(str(bundle_dir / "ui-recruitment_assets_all.bundle"))
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        raw = obj.get_raw_data()
        if len(raw) > 32:
            nlen = struct.unpack_from("<i", raw, 28)[0]
            if 0 < nlen < 200:
                name = raw[32 : 32 + nlen].decode("utf-8", errors="replace")
                if "Priorit" in name or "Scout" in name or "Focus" in name:
                    print(f"PathID={obj.path_id} size={len(raw)} name={name!r}")
                elif b"ScoutPriorities" in raw or b"scoutpriorities" in raw.lower():
                    print(f"PathID={obj.path_id} size={len(raw)} name={name!r} (contains ScoutPriorities)")
