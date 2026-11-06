import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from walk_st import raw, walk_node

# Also map factory GUIDs to factory names!
# Wait, how are GUIDs mapped to PathIDs/names in Addressables catalog or bundle?
# Let's print all 38 StreamedTables in ui-recruitment_assets_all.bundle first.
pos = 0
target = b"StreamedTable/UxmlSerializedData"
while True:
    idx = raw.find(target, pos)
    if idx < 0:
        break
    # Find enclosing asset name by searching backwards for MonoBehaviour m_Name or VisualTreeAsset name
    # Actually let's check strings before idx
    try:
        _, obj = walk_node(raw, idx + 0x44, 0)
        init_fn = obj.get("InitFunction", {}).get("m_MethodAssetGUID", "")
        init_args = [x.get("m_Name", "") for x in obj.get("InitFunction", {}).get("m_Inputs", [])]
        print(
            f"Off {idx:7d} (0x{idx:06x}): "
            f"DisSort={obj.get('DisableSorting')} "
            f"Reord={obj.get('Reorderable')} "
            f"Bind={obj.get('Binding')!r} "
            f"SortBind={obj.get('SortBinding')!r} "
            f"DragCell={obj.get('DragCellID')!r} "
            f"RemCell={obj.get('RemoveCellID')!r} "
            f"Fac={obj.get('FactoryAsset', {}).get('m_AssetGUID', '')[:8]} "
            f"Init={init_fn[:8]}({','.join(init_args)})"
        )
    except Exception as e:
        print(f"Off {idx:7d}: ERR {e}")
    pos = idx + len(target)
