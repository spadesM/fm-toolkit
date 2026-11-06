import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
import UnityPy

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

for b in sorted(aa_dir.glob("ui-*.bundle")):
    if any(k in b.name for k in ("recruit", "scout", "tile", "table", "panel", "card")):
        print("Bundle:", b.name)

env = UnityPy.load(str(aa_dir / "ui-recruitment_assets_all.bundle"))
print("\n=== VisualTreeAssets in ui-recruitment_assets_all.bundle ===")
for i, obj in enumerate(env.objects):
    if obj.type.name == "MonoBehaviour":
        raw = obj.get_raw_data()
        if len(raw) >= 32:
            import struct
            name_len = struct.unpack_from("<I", raw, 28)[0]
            if 0 < name_len < 200 and 32 + name_len <= len(raw):
                name = raw[32:32+name_len].decode("utf-8", errors="replace")
                print(f"  Obj {i} (pid={obj.path_id}): {name}")
