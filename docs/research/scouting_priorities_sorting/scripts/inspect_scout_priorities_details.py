import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

def inspect_bundle_obj(bname, target_names):
    raw, trees, objs, ref_trees = parse_bundle_with_reftypes(bname)
    for oi, pid, abs_off, bsize, tid in objs:
        chunk = raw[abs_off : abs_off + bsize]
        if bsize < 36:
            continue
        ln = struct.unpack_from("<I", chunk, 28)[0]
        if 0 < ln < 200:
            name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
        else:
            ln2 = struct.unpack_from("<I", chunk, 0)[0]
            name = chunk[4 : 4 + ln2].decode("utf-8", errors="replace") if 0 < ln2 < 200 else ""
        if any(t in name for t in target_names):
            cid, nodes = trees[tid]
            print(f"\n=== {bname} | Obj {oi} | pid={pid} | cid={cid} | name='{name}' ===")
            try:
                _, val = walk_tree(nodes, chunk, 0, 0)
                if isinstance(val, dict):
                    for k, v in val.items():
                        if k == "m_VisualElementAssets":
                            print(f"  m_VisualElementAssets ({len(v)}):")
                            for ve in v:
                                print(f"    id={ve.get('m_Id')} parent={ve.get('m_ParentId')} type={ve.get('m_FullTypeName')} name={ve.get('m_Name')} classes={ve.get('m_Classes')}")
                        elif k == "m_TemplateAssets":
                            print(f"  m_TemplateAssets ({len(v)}):")
                            for ta in v:
                                print(f"    id={ta.get('m_Id')} parent={ta.get('m_ParentId')} alias={ta.get('m_TemplateAlias')} asset={ta.get('m_Template')}")
                        elif k not in ("m_SerializedData", "m_ContentHash", "m_ inlineSheet"):
                            print(f"  {k}: {v}")
            except Exception as e:
                print(f"  walk_tree err: {e}")

inspect_bundle_obj("ui-recruitment_assets_all.bundle", ["ScoutPriorities", "Priorities"])
inspect_bundle_obj("ui-tiles_assets_all.bundle", ["ScoutPriorities"])
inspect_bundle_obj("ui-tableviews_assets_all.bundle", ["ScoutPriorities"])
inspect_bundle_obj("ui-tablefactories_assets_all.bundle", ["SpecificallyScouted", "PlayerTableFactory"])

meta = dhf.meta
for term in [b"SpecificallyScoutedPlayers", b"ScoutPriorities", b"SpecificallyScouted", b"OverallReportGradeInfo"]:
    print(f"\n--- Metadata matches for {term.decode()} ---")
    pos = 0
    while True:
        idx = meta.find(term, pos)
        if idx == -1:
            break
        start = max(0, idx - 24)
        end = min(len(meta), idx + 64)
        print(f"  @0x{idx:x}: {meta[start:end]!r}")
        pos = idx + len(term)
