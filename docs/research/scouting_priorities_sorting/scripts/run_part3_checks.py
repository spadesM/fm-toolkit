import struct, sys

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\part3_checks_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 3. Dump SpecificallyScoutedPersonReference & Related Types ===")
hdr = struct.unpack("<64I", meta[:256])
types_sz = hdr[41]
num_types = types_sz // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if any(k in tname for k in ("SpecificallyScouted", "ScoutPriorities", "ScoutingPriorities")):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (methods={m_cnt})")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            found_rvas = [r for r, nms in rva_to_method_name.items() if f"{tname}.{mname}" in nms]
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in found_rvas]}")
            for r in found_rvas:
                sz = min(rva_to_end.get(r, r + 600) - r, 900)
                dump_func_details(f"{tname}.{mname}", r, sz)

print("\n=== 4. SpecificallyScoutedTeamTableFactory vs SpecificallyScoutedPersonTableFactory ===")
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs:
    if oi in (92, 232, 118, 31):
        _, nodes = trees[tid]
        chunk = raw[abs_off : abs_off + bsize]
        _, props = walk_tree(nodes, chunk, 0, 0)
        name = props.get("m_Name", props.get("common_427", ""))
        rds = props.get("m_rowData", [])
        print(f"\nFactory Obj {oi:3d} ({name}): params={props.get('m_parameters')} ctxPath={props.get('m_contextMenuBindingPath')}")
        for rd in rds:
            print(f"  id={rd.get('m_id'):22s} sort={rd.get('m_sortBinding', {}).get('m_path')!r:65s} asc={rd.get('m_sortAscending')} plug={rd.get('m_sortBindingPlugin')} valBinds={[(vb.get('from'), vb.get('to', {}).get('m_path'), vb.get('type')) for vb in rd.get('m_valueBindings', [])]}")

print("\n=== 5. Dump UXML Assets in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_r:
    if oi in (177, 229, 263, 360):
        _, nodes = trees_r[tid]
        chunk = raw_r[abs_off : abs_off + bsize]
        _, props = walk_tree(nodes, chunk, 0, 0)
        print(f"\n--- UXML Obj {oi} (pid={pid}, name={props.get('m_Name', props.get('common_427'))}) ---")
        for ve in props.get("m_VisualElementAssets", props.get("common_540", [])):
            print(f"  VE {ve}")

out_file.close()
