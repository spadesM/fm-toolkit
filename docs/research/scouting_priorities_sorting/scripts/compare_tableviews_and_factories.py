import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes

bundle_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64"
tv_objs = parse_bundle_with_reftypes(bundle_dir + r"\ui-tableviews_assets_all.bundle")

for pid, (cname, val) in tv_objs.items():
    if isinstance(val, dict):
        name = val.get("m_Name", "")
        if any(k in name.lower() for k in ("scoutpriorit", "recommendation", "shortlist", "playersearch", "playerdatabase")):
            print(f"\n=== [PathID {pid}] ({cname}) {name} ===")
            for k, v in val.items():
                if k in ("m_Script", "m_GameObject", "m_Enabled"):
                    continue
                print(f"  {k}: {v}")
