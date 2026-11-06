import struct, sys

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\remaining_checks_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. VirtualisedList.m_reorderable (+0x5c1) ===")
off_start = va_to_off(image_base + 0x016a7000)
off_end = va_to_off(image_base + 0x016ae000)
chunk = pe[off_start:off_end]
pos = 0
while True:
    idx = chunk.find(b"\xc1\x05\x00\x00", pos)
    if idx == -1:
        break
    rva = 0x016a7000 + idx
    fn_rva = max((k for k in rva_to_end if k <= rva), default=0)
    print(f"Found +0x5c1 at RVA=0x{rva:08x} in {rva_to_method_name.get(fn_rva)} (0x{fn_rva:08x})")
    dump_func_details(f"Reorderable ref {rva_to_method_name.get(fn_rva)}", fn_rva, 300)
    pos = idx + 1

print("\n=== 2. Dump SetSorting<T> (0x00abdcc0, 750) ===")
dump_func_details("SetSorting<T>", 0x00abdcc0, 750)

print("\n=== 3. Dump StreamedTable.TrySetColumnsAndSort (0x015f0040, 1200) ===")
dump_func_details("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 1200)

print("\n=== 4. Dump StreamedTable.UpdateStreamedTableView (0x015f1650, 400) ===")
dump_func_details("StreamedTable.UpdateStreamedTableView", 0x015f1650, 400)

print("\n=== 5. Dump Bindings.SetAlias (0x014c3050, 400) ===")
dump_func_details("Bindings.SetAlias", 0x014c3050, 400)

print("\n=== 6. Dump Bindings.OnNodeCreated (0x014c6590, 500) ===")
dump_func_details("Bindings.OnNodeCreated", 0x014c6590, 500)

print("\n=== 7. Dump Bindings.Update part 1 (0x014c6a70, 3050) ===")
dump_func_details("Bindings.Update_part1", 0x014c6a70, 3050)

print("\n=== 8. Dump SpecificallyScoutedPersonReference & Related Types ===")
hdr = struct.unpack("<64i", meta[:256])
types_sz = hdr[41]
num_types = types_sz // 88
for ti in range(num_types):
    t_off = types_off + ti * 88
    vals = struct.unpack("<22I", meta[t_off:t_off+88])
    tname = get_mstr(vals[0])
    tns = get_mstr(vals[1])
    if any(k in tname for k in ("SpecificallyScouted", "ScoutPriorities", "ScoutingPriorities")):
        m_first = vals[9]
        m_count = vals[17] & 0xFFFF
        f_first = vals[7]
        f_count = vals[16] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (fields={f_count}, methods={m_count})")
        for fi in range(f_first, f_first + f_count):
            foff = fields_off + fi * 12
            fn_idx, ft_idx, f_tok = struct.unpack("<3I", meta[foff:foff+12])
            print(f"  Field {fi - f_first}: {get_mstr(fn_idx)}")
        for mi in range(m_first, m_first + m_count):
            moff = methods_off + mi * 32
            mvals = struct.unpack("<8I", meta[moff:moff+32])
            mname = get_mstr(mvals[0])
            mrva = rva_to_method_name
            # find RVA from rva_to_method_name or dump
            found_rvas = [r for r, nm in rva_to_method_name.items() if nm == f"{tname}.{mname}"]
            print(f"  Method {mi - m_first}: {mname} RVAs={[hex(r) for r in found_rvas]}")
            for r in found_rvas:
                sz = min(rva_to_end.get(r, r + 500) - r, 800)
                dump_func_details(f"{tname}.{mname}", r, sz)

print("\n=== 9. SpecificallyScoutedTeamTableFactory vs SpecificallyScoutedPersonTableFactory ===")
raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs:
    if oi in (92, 232, 118, 31):
        _, nodes = trees[tid]
        top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
        p = abs_off
        props = {}
        for c in top_children:
            cname = nodes[c][3]
            try:
                p_next, val = walk_tree(nodes, raw, p, c)
                props[cname] = val
                p = p_next
            except Exception:
                break
        name = props.get("common_427", "")
        rds = props.get("m_rowData", [])
        print(f"\nFactory Obj {oi:3d} ({name}): params={props.get('m_parameters')} ctxPath={props.get('m_contextMenuBindingPath')}")
        for rd in rds:
            print(f"  id={rd.get('m_id'):22s} sort={rd.get('m_sortBinding', {}).get('m_path')!r:65s} asc={rd.get('m_sortAscending')} plug={rd.get('m_sortBindingPlugin')} valBinds={[(vb.get('from'), vb.get('to', {}).get('m_path'), vb.get('type')) for vb in rd.get('m_valueBindings', [])]}")

out_file.close()
