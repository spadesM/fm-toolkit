import UnityPy
import os
import json

aa_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64"

def check_recruitment_tables():
    env = UnityPy.load(os.path.join(aa_dir, "ui-recruitment_assets_all.bundle"))
    for obj in env.objects:
        if obj.type.name == "VisualTreeAsset":
            data = obj.read()
            name = getattr(data, "m_Name", "")
            if any(k in name for k in ["ScoutPriorit", "ShortlistMain", "RecruitmentFocus", "PlayerSearch", "Database"]):
                tt = obj.read_typetree()
                uxml = tt.get("m_UxmlObjectEntries", [])
                print(f"=== VTA {obj.path_id}: {name} ===")
                for entry in uxml:
                    for d in entry.get("uxmlObjectAssets", []):
                        full_name = d.get("fullTypeName", "")
                        if "StreamedTable/UxmlSerializedData" in full_name or "StreamedListView/UxmlSerializedData" in full_name:
                            print(f"  [{full_name}]")
                            for k, v in d.items():
                                if not k.endswith("_UxmlAttributeFlags") and k not in ("fullTypeName", "uxmlObjectId", "serializedDataId"):
                                    print(f"    {k}: {v}")

if __name__ == "__main__":
    check_recruitment_tables()
