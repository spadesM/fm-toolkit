import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
from check_deep_sorting import dump_func_details, pe, va_to_off, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi in (229, 263, 111, 103):
    _, pid, abs_off, bsize, tid = objs[oi]
    chunk = raw[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    if idx != -1:
        # Find exact data start after class/ns/asm strings (aligned to 4)
        p0 = idx
        for _ in range(3):
            e = chunk.find(b"\x00", p0)
            p0 = e + 1
            # Wait, Unity's ReferencedObjectType stores 3 length-prefixed strings!
        # Let's check how compare_full_st_serialized_data parses it
        pass

# Let's search all types in all images for ScoutPriorit / SpecificallyScouted / ScoutedPerson
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if iname not in modules: continue
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        ns = get_mstr(tu[1])
        if any(k in tname for k in ("SpecificallyScouted", "ScoutPriorit", "ScoutAssignment", "ScoutingCentreEntry")):
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"\n=== [{iname}] {ns}.{tname} (type {ti}) ===")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")
