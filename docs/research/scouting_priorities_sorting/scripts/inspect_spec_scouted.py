import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import check_deep_sorting as cds

# 1. Check ScoutPrioritiesTable & SpecificallyScoutedPersonTableFactory
raw_tv, trees_tv, objs_tv, _ = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_tv:
    if pid in (6820118260298404215, 7446456543218343850):
        chunk = raw_tv[abs_off : abs_off + bsize]
        _, val = walk_tree(trees_tv[tid][1], chunk, 0, 0)
        print(f"=== TableView {val.get('common_427')} ({pid}) ===")
        for k, v in val.items():
            print(f"  {k}: {v}")

raw_tf, trees_tf, objs_tf, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_tf:
    if pid in (-2280246386909779364, -6813643292728705340):
        chunk = raw_tf[abs_off : abs_off + bsize]
        _, val = walk_tree(trees_tf[tid][1], chunk, 0, 0)
        name = val.get("common_427")
        cols = val.get("m_columns", [])
        print(f"\n=== TableFactory {name} ({pid}) - {len(cols)} columns ===")
        if name == "SpecificallyScoutedPersonTableFactory":
            for c in cols:
                vb = [(b.get("from"), b.get("to", {}).get("m_path")) for b in c.get("m_valueBindings", [])]
                print(f"  col id='{c.get('m_id')}' sort='{c.get('m_sortBinding', {}).get('m_path')}' plugin={c.get('m_sortBindingPlugin')} asc={c.get('m_sortAscending')} vbinds={vb}")
        else:
            # Map PlayerTableFactory columns by id for comparison
            ptf_map = {c.get("m_id"): c for c in cols}

print("\n=== Comparing SpecificallyScoutedPersonTableFactory vs PlayerTableFactory ===")
for oi, pid, abs_off, bsize, tid in objs_tf:
    if pid == -2280246386909779364:
        chunk = raw_tf[abs_off : abs_off + bsize]
        _, val = walk_tree(trees_tf[tid][1], chunk, 0, 0)
        for c in val.get("m_columns", []):
            cid = c.get("m_id")
            s1 = c.get("m_sortBinding", {}).get("m_path")
            vb1 = [(b.get("from"), b.get("to", {}).get("m_path")) for b in c.get("m_valueBindings", [])]
            pc = ptf_map.get(cid)
            if pc:
                s2 = pc.get("m_sortBinding", {}).get("m_path")
                vb2 = [(b.get("from"), b.get("to", {}).get("m_path")) for b in pc.get("m_valueBindings", [])]
                if s1 != s2 or vb1 != vb2 or not s1:
                    print(f"  [{cid}] SpecScout sort='{s1}' vb={vb1}  |  PlayerTF sort='{s2}' vb={vb2}")
            else:
                print(f"  [{cid}] (ONLY in SpecScout) sort='{s1}' vb={vb1}")

# 2. Search types and methods in global-metadata.dat
meta = cds.meta
hdr = cds.hdr
types_off, types_sz = hdr[40], hdr[41]
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[24], hdr[25]
props_off, props_sz = hdr[16], hdr[17]

for img_i in range(cds.images_sz // 40):
    iu = struct.unpack_from("<10i", meta, cds.images_off + img_i * 40)
    iname = cds.get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = cds.get_mstr(tu[0])
        ns = cds.get_mstr(tu[1])
        if any(w in tname for w in ["SpecificallyScouted", "ScoutPriorit", "ScoutAssignment"]):
            print(f"\n=== Type {ti} ({iname}): {ns}.{tname} ===")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            _, m_cnt_mod, m_ptrs_va = cds.modules.get(iname, (0, 0, 0))
            ptrs_off = cds.va_to_off(m_ptrs_va) if m_ptrs_va else -1
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = cds.get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", cds.pe, ptrs_off + rid * 8)[0] if (ptrs_off >= 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - cds.image_base if va else 0
                print(f"  Method {mi}: {mname} (RVA=0x{rva:08x})")
