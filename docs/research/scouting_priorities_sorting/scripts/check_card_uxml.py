import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
rec_raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")

# 1. Inspect strings around 1949376 (RecruitmentScoutPrioritiesCard) in ui-recruitment_assets_all.bundle
print("=== Strings in RecruitmentScoutPrioritiesCard (1949376..1960000) ===")
chunk = rec_raw[1949376 : 1960000]
import re
for m in re.finditer(rb"[ -~]{4,}", chunk):
    print(f"  +{m.start():5d} (0x{1949376+m.start():x}): {m.group().decode('ascii', errors='replace')}")

# 2. Check all occurrences of StreamedTable/UxmlSerializedData in ui-recruitment_assets_all.bundle
needle = b"SI.Bindable.StreamedTable/UxmlSerializedData"
pos = 0
print("\n=== All StreamedTable/UxmlSerializedData in ui-recruitment_assets_all.bundle ===")
while True:
    idx = rec_raw.find(needle, pos)
    if idx < 0:
        break
    # find nearest asset name before idx
    print(f"  StreamedTable/UxmlSerializedData at {idx} (0x{idx:x})")
    pos = idx + 1
