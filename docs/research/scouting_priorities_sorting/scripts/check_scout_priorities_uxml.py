import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, r"c:\Repos\fm26save")
from inspect_vta_refs_and_props import raw, trees, objs, walk_tree, dump_vta_refs

def dump_full_vta(obj_idx):
    oi, pid, abs_off, bsize, tid = objs[obj_idx]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {}
    for c in top_children:
        cname = nodes[c][3]
        if cname == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[cname] = val
    print(f"\n=======================================================")
    print(f"=== Obj {obj_idx} (pid={pid}, name={res.get('common_427')}) ===")
    print(f"=======================================================")
    for ve in res.get("m_VisualElementAssets", []):
        print(f"  VE id={ve.get('m_Id')} parent={ve.get('m_ParentId')} order={ve.get('m_OrderInDocument')} type={ve.get('m_FullTypeName')} classes={ve.get('m_Classes')} props={ve.get('m_Properties')} sd={ve.get('m_SerializedData')}")
    for te in res.get("m_TemplateAssets", []):
        print(f"  TE id={te.get('m_Id')} parent={te.get('m_ParentId')} order={te.get('m_OrderInDocument')} alias={te.get('m_TemplateAlias')} props={te.get('m_Properties')} sd={te.get('m_SerializedData')}")
    for uo in res.get("m_UxmlObjectEntries", []):
        print(f"  UO parent={uo.get('parentId')} assets={uo.get('uxmlObjectAssets')}")
    dump_vta_refs(obj_idx)

for idx in (177, 229, 263, 103):
    dump_full_vta(idx)
