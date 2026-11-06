import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

def inspect_vta_safe(bname, target_names):
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    for oi, pid, abs_off, bsize, tid in objs:
        chunk = raw[abs_off : abs_off + bsize]
        if bsize < 36:
            continue
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else ""
        if any(t in name for t in target_names):
            cid, nodes = trees[tid]
            print(f"\n=== {bname} | Obj {oi} | pid={pid} | name='{name}' ===")
            top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
            p = 0
            for c in top_children:
                cname = nodes[c][3]
                if cname in ("m_VisualElementAssets", "m_TemplateAssets", "m_UxmlObjectEntries", "m_UsingEntries"):
                    try:
                        p, val = walk_tree(nodes, chunk, p, c)
                        print(f"  {cname} ({len(val)}):")
                        for item in val:
                            if cname == "m_VisualElementAssets":
                                print(f"    VE id={item.get('m_Id')} order={item.get('m_OrderInDocument')} parent={item.get('m_ParentId')} type={item.get('m_FullTypeName')} name='{item.get('m_Name')}' classes={item.get('m_Classes')} props={item.get('m_Properties')}")
                            else:
                                print(f"    {item}")
                    except Exception as e:
                        print(f"  Err at {cname}: {e}")
                        break
                else:
                    try:
                        p, val = walk_tree(nodes, chunk, p, c)
                    except Exception as e:
                        print(f"  Err at {cname}: {e}")
                        break

inspect_vta_safe("ui-recruitment_assets_all.bundle", ["ScoutPriorities", "Priorities"])
inspect_vta_safe("ui-tiles_assets_all.bundle", ["ScoutPriorities"])
inspect_vta_safe("ui-panelids-uxml_assets_all.bundle", ["SpecificallyScouted"])
