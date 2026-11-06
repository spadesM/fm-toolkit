import struct, sys, glob, os
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm4.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Inspect All Methods of SpecificallyScoutedPersonReference (Type 909 in FM.UI.dll) ===")
hdr = struct.unpack_from("<64I", meta, 0)
real_fields_off = hdr[24]
_, m_cnt_mod, m_ptrs_va = modules["FM.UI.dll"]
ptrs_off = va_to_off(m_ptrs_va)

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "FM.UI.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if "SpecificallyScouted" in tname or "ScoutPriorit" in tname:
                f_start, f_cnt = tu[8], tu[17] & 0xFFFF
                m_start, m_cnt = tu[9], tu[16] & 0xFFFF
                print(f"\n--- Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
                for fi in range(f_start, f_start + f_cnt):
                    fu = struct.unpack_from("<3i", meta, real_fields_off + fi * 12)
                    print(f"  Field {fi - f_start:2d}: {get_mstr(fu[0])}")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                    rva = va - image_base if va else 0
                    print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")
                    if rva > 0:
                        end_rva = rva_to_end.get(rva, rva + 0x150)
                        dump_fast(f"{tname}.{mname}", rva, end_rva)

print("\n=== 2. Disassemble Bindings.BindProperty_internal (0x014beef0) and StreamedTable.UpdateSortedColumns (0x015f1380) ===")
for name, rva in [
    ("Bindings.BindProperty_1746", 0x014beef0),
    ("StreamedTable.UpdateSortedColumns", 0x015f1380),
    ("StreamedTable.SaveSortedColumnsToPersistence", 0x015f1290),
    ("StreamedTable.GetRowData", 0x015e9450),
    ("StreamedListView.MarkDirty", 0x015a9780),
    ("StreamedListView.BeginStateChange", 0x015a47a0),
]:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dump_fast(name, rva, end_rva)

print("\n=== 3. Compare All StreamedTable/UxmlSerializedData in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees_r["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_r):
    chunk = raw_r[abs_off : abs_off + bsize]
    pat = b"StreamedTable/UxmlSerializedData"
    pos = 0
    while True:
        idx = chunk.find(pat, pos)
        if idx == -1:
            break
        ln = struct.unpack_from("<I", chunk, 28)[0]
        name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if ln < 200 else f"Obj_{oi}"
        print(f"\n--- Obj {oi} ({name}) at +0x{idx:x} ---")
        p = idx + 64
        for c in top_children:
            cname = st_nodes[c][3]
            try:
                p_next, val = walk_tree(st_nodes, chunk, p, c)
                if cname in ("Binding", "SortBinding", "FactoryAsset", "InitFunction", "DisableSorting", "Reorderable", "DragCellID", "SelectionType", "SortedColumn") or (
                    not cname.endswith("_UxmlAttributeFlags") and val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2)
                ):
                    print(f"  {cname}: {val}")
                p = p_next
            except Exception as e:
                print(f"  ERROR at {cname}: {e}")
                break
        pos = idx + 64

out_file.close()
