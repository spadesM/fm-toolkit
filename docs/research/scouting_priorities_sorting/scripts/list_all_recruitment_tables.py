import sys
sys.stdout.reconfigure(encoding="utf-8")
import UnityPy

bundle_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64\ui-recruitment_assets_all.bundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        data = obj.read()
        if hasattr(data, "m_Name"):
            tt = obj.read_typetree()
            elem_defs = tt.get("m_UxmlObjectEntries", [])
            # or check serialized data
            raw = obj.get_raw_data()
            if b"StreamedTable" in raw:
                print(f"Obj {obj.path_id}: {data.m_Name}")
                for entry in tt.get("m_UxmlElementEntries", []):
                    pass
