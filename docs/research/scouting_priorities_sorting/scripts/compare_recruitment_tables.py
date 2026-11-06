import UnityPy, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
aa = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

env_rec = UnityPy.load(str(aa / "ui-recruitment_assets_all.bundle"))
env_tv = UnityPy.load(str(aa / "ui-tableviews_assets_all.bundle"))
env_tf = UnityPy.load(str(aa / "ui-tablefactories_assets_all.bundle"))

# Map GUIDs or PathIDs? Wait: let's inspect all MonoBehaviours in env_tf and env_tv by name/PathID
tf_by_name = {}
for obj in env_tf.objects:
    if obj.type.name == "MonoBehaviour":
        d = obj.read_typetree()
        tf_by_name[d.get("m_Name", "")] = d

tv_by_name = {}
for obj in env_tv.objects:
    if obj.type.name == "MonoBehaviour":
        d = obj.read_typetree()
        tv_by_name[d.get("m_Name", "")] = d

print(f"Loaded {len(tf_by_name)} table factories, {len(tv_by_name)} table views/collections.")

for obj in env_rec.objects:
    if obj.type.name == "MonoBehaviour":
        d = obj.read_typetree()
        name = d.get("m_Name", "")
        vas = d.get("m_VisualElementAssets", [])
        for va in vas:
            fn = va.get("m_FullTypeName", "")
            if "StreamedTable" in fn:
                sd = va.get("m_SerializedData", {})
                print(f"\n=== {name} (PathID={obj.path_id}) -> {va.get('m_Name')} ({fn}) ===")
                for k, v in sd.items():
                    if not k.endswith("_UxmlAttributeFlags") and k not in ("Classes", "Name", "RuleIndex", "PickingMode", "UsageHints", "TabIndex", "Focusable", "Tooltip", "ViewDataKey", "LanguageDirection", "DataSourcePath", "FillAvailableSpace", "EmptyText", "EmptyTextTranslationID"):
                        print(f"  {k}: {v}")
