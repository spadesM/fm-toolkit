import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root
from list_recruitment_objs import parse_bundle_clean
from compare_all_aspects import read_typetree

aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

for bname, target_id in [("ui-tablefactories_assets_all.bundle", 14), ("ui-tableviews_assets_all.bundle", 7)]:
    raw, trees, objs = parse_bundle_clean(aa_dir / bname)
    for o in objs:
        if o["path_id"] == target_id:
            val, _ = read_typetree(raw, o["offset"], trees[o["type_idx"]][0])
            print(f"=== {bname} Obj {target_id}: {val.get('m_Name')} ===")
            if "m_tableMetadata" in val:
                for i, col in enumerate(val["m_tableMetadata"]):
                    cid = col.get("m_columnID")
                    sbind = col.get("m_sortBinding", {}).get("m_path", "")
                    sdis = col.get("m_sortingDisabled")
                    hdr = col.get("m_headerText", {}).get("m_stringID", "")
                    cell_guid = col.get("m_cell", {}).get("m_AssetGUID", "")
                    print(f"  Col {i:2d}: id={cid!r:35s} sortBinding={sbind!r:40s} sortingDisabled={sdis} hdr={hdr!r} cell={cell_guid}")
            if "m_tableViews" in val:
                for i, tv in enumerate(val["m_tableViews"]):
                    print(f"  View {i}: name={tv.get('m_viewName')!r}")
                    for j, c in enumerate(tv.get("m_tableView", [])):
                        print(f"    [{j:2d}] col={c.get('m_columnID')!r:35s} req={c.get('m_required')} width={c.get('m_overrideWidth')}")
