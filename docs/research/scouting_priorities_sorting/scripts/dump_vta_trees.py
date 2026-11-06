import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from parse_recruitment_objs import raw, objs, trees
from check_tvc import walk_tree

vta_nodes = trees[0]
for target_oi in (177, 229, 263, 144, 360):
    oi, path_id, abs_off, byte_size, type_id, name = objs[target_oi]
    print(f"\n==================== Obj {oi}: {name} (PathID={path_id}) ====================")
    _, obj = walk_tree(vta_nodes, raw, abs_off)
    for k, v in obj.items():
        if k in ("m_VisualElementAssets", "m_TemplateAssets"):
            print(f"  {k} ({len(v)}):")
            for item in v:
                print(f"    id={item.get('m_Id')} parent={item.get('m_ParentId')} name={item.get('m_Name')!r} type={item.get('m_FullTypeName')!r} classes={item.get('m_Classes')}")
                sd = item.get("m_SerializedData", {})
                if sd:
                    print(f"      serializedData: {sd}")
        elif k == "m_UxmlObjectEntries":
            print(f"  {k} ({len(v)}):")
            for entry in v:
                print(f"    parentId={entry.get('parentId')} entries={len(entry.get('uxmlObjectAssets', []))}")
                for ua in entry.get("uxmlObjectAssets", []):
                    print(f"      type={ua.get('m_FullTypeName')!r} data={ua.get('m_SerializedData')}")
        else:
            print(f"  {k}: {v}")
