import struct, sys, glob, os
sys.stdout.reconfigure(encoding="utf-8")
from compare_full_st_serialized_data import parse_bundle_with_reftypes, aa_dir
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

# Find all objects in ui-recruitment_assets_all.bundle that mention ScoutPriorities or SpecificallyScouted
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs):
    chunk = raw[abs_off : abs_off + bsize]
    if b"ScoutPriorities" in chunk or b"SpecificallyScouted" in chunk or b"399c0aa9357f67847b91ba2fe4756083" in chunk or b"13a1f18bd93e860488c2cb84abb1168c" in chunk:
        tname, nodes = trees[tid]
        top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
        p = abs_off
        props = {}
        for c in top_children:
            cname = nodes[c][3]
            try:
                p_next, val = walk_tree(nodes, raw, p, c)
                props[cname] = val
                p = p_next
            except Exception as e:
                props[cname] = f"ERR:{e}"
                break
        print(f"\n=== Obj {oi} (PathID={pid}, Type={tname}, Name={props.get('m_Name')}) ===")
        for k, v in props.items():
            if k == "m_VisualElementAssets":
                print(f"  m_VisualElementAssets ({len(v)}):")
                for ve in v:
                    print(f"    id={ve.get('m_Id')} parent={ve.get('m_ParentId')} order={ve.get('m_OrderInDocument')} type={ve.get('m_FullTypeName')} name={ve.get('m_Name')} classes={ve.get('m_Classes')} ruleIndex={ve.get('m_RuleIndex')}")
            elif k == "m_TemplateAssets":
                print(f"  m_TemplateAssets ({len(v)}):")
                for ta in v:
                    print(f"    id={ta.get('m_Id')} parent={ta.get('m_ParentId')} order={ta.get('m_OrderInDocument')} alias={ta.get('m_TemplateAlias')}igs={ta.get('m_AttributeOverrides')}")
            elif k == "m_Using":
                print(f"  m_Using: {v}")
            elif k not in ("m_ClearFlags",):
                print(f"  {k}: {str(v)[:300]}")
