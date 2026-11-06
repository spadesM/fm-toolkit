import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, hdr, types_off, types_sz, methods_off, fields_off, get_mstr, va_to_off, off_to_va,
    image_base, rva_to_end, rva_to_method_name, dump_func_details
)
from annotate_sorting_usym import dump_annotated
from compare_full_st_serialized_data import parse_bundle_with_reftypes, walk_tree

# 1. Print all methods and fields of target TypeDefs
for ti in (860, 909, 5791, 5967, 13468):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    f_first, m_first = tu[8], tu[9]
    f_cnt = tu[16] & 0xFFFF
    m_cnt = (tu[16] >> 16) & 0xFFFF
    print(f"=== TypeDef {ti}: {tns}.{tname} (fields={f_cnt} from {f_first}, methods={m_cnt} from {m_first}) ===")
    if f_first >= 0:
        for fi in range(f_first, f_first + f_cnt):
            f_name_idx, f_type_idx, f_token = struct.unpack_from("<3i", meta, fields_off + fi * 12)
            print(f"  Field {fi - f_first}: {get_mstr(f_name_idx)} (type_idx={f_type_idx})")
    if m_first >= 0:
        for mi in range(m_first, m_first + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            # find RVA from rva_to_method_name
            print(f"  Method {mi}: {mname} (params={mu[10]})")

# Also let's print all RVAs in rva_to_method_name for VirtualisedList, ScoutPlayerPrioritiesReference, SpecificallyScoutedPersonReference
print("\n=== Method RVAs ===")
for rva, mnames in sorted(rva_to_method_name.items()):
    for mn in mnames:
        if any(mn.startswith(p) for p in ("VirtualisedList.", "ScoutPlayerPrioritiesReference.", "SpecificallyScoutedPersonReference.", "StreamedListView.", "StreamedTable.")):
            print(f"  0x{rva:08x}: {mn}")

# 2. Dump UXML hierarchy of Obj 177, 229, 263, 103
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oid in (177, 229, 263, 103):
    idx, pid, off, sz, tid = objs[oid]
    cid, nodes = trees[tid]
    val, _ = walk_tree(raw, off, nodes, 0, ref_trees)
    print(f"\n================ Object {oid} (pid={pid}): {val.get('common_494')} ================")
    for ve in val.get("m_VisualElementAssets", []):
        print(f"  VE id={ve.get('m_Id')} parent={ve.get('m_ParentId')} order={ve.get('m_OrderInDocument')} type={ve.get('m_FullTypeName')} name={ve.get('common_494')} classes={ve.get('m_Classes')}")
        sd = ve.get("m_SerializedData", {})
        if isinstance(sd, dict) and "data" in sd and isinstance(sd["data"], dict):
            d = sd["data"]
            interesting = {}
            for k, v in d.items():
                if k.endswith("_UxmlAttributeFlags") and v != 0:
                    base_k = k[:-len("_UxmlAttributeFlags")]
                    interesting[base_k] = d.get(base_k)
            if interesting:
                print(f"    Active attributes: {interesting}")
    for ta in val.get("m_TemplateAssets", []):
        print(f"  TA id={ta.get('m_Id')} parent={ta.get('m_ParentId')} order={ta.get('m_OrderInDocument')} alias={ta.get('m_TemplateAlias')} name={ta.get('common_494')} classes={ta.get('m_Classes')}")
        sd = ta.get("m_SerializedData", {})
        if isinstance(sd, dict) and "data" in sd and isinstance(sd["data"], dict):
            d = sd["data"]
            interesting = {}
            for k, v in d.items():
                if k.endswith("_UxmlAttributeFlags") and v != 0:
                    base_k = k[:-len("_UxmlAttributeFlags")]
                    interesting[base_k] = d.get(base_k)
            if interesting:
                print(f"    Active attributes: {interesting}")
        for ao in ta.get("m_AttributeOverrides", []):
            print(f"    AttrOverride: {ao}")
        for so in ta.get("m_SerializedDataOverrides", []):
            print(f"    SerializedDataOverride: {so}")
    for uo in val.get("m_UxmlObjectEntries", []):
        print(f"  UxmlObject parentId={uo.get('parentId')}:")
        for uoa in uo.get("uxmlObjectAssets", []):
            print(f"    UxmlObjectAsset fullTypeName={uoa.get('m_FullTypeName')} isField={uoa.get('m_IsField')} sd={uoa.get('m_SerializedData')}")
