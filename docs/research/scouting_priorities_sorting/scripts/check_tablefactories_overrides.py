import UnityPy

bundle_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64\ui-tablefactories_assets_all.bundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        d = obj.read_typetree()
        name = d.get("m_Name", "")
        if "TableFactory" in name or "Scout" in name or "Player" in name or "Priority" in name or "Shortlist" in name:
            params = d.get("m_parameters", [])
            cols = d.get("m_columns", [])
            sample_overrides = []
            for c in cols[:12]:
                cid = c.get("m_id", "")
                so = c.get("m_sortingOverride", {}).get("m_path", "")
                sv = c.get("m_sortingValue", 0)
                if so or sv:
                    sample_overrides.append(f"{cid}: override='{so}' val={sv}")
            print(f"Obj {obj.path_id} ({name}): params={params}")
            for s in sample_overrides[:8]:
                print(f"   {s}")
