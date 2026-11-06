import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root
from list_recruitment_objs import parse_bundle_clean

aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"
for b in sorted(aa_dir.glob("ui-*.bundle")):
    data = b.read_bytes()
    # Quick check or unpack if ui-tiles*
    if "tile" in b.name or "recruitment" in b.name or "panel" in b.name or "card" in b.name or "table" in b.name:
        try:
            raw, trees, objs = parse_bundle_clean(b.name)
            for target in (b"RecruitmentFocusToolTableBlock", b"ScoutPrioritiesTile", b"ScoutPrioritiesBlock"):
                if target in raw:
                    print(f"Found {target.decode()} in {b.name}!")
        except Exception as e:
            pass
