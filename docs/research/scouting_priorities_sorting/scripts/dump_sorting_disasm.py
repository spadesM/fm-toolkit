import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm2.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

hdr = struct.unpack_from("<64I", meta, 0)
real_fields_off = hdr[24]
num_types_defs = hdr[41] // 88

# Locate fieldOffsets table
pattern = struct.pack("<Q", num_types_defs)
pos = 0
field_offsets_table_off = -1
while True:
    idx = pe.find(pattern, pos)
    if idx < 0:
        break
    if idx + 32 <= len(pe):
        c1, p1, c2, p2 = struct.unpack_from("<4Q", pe, idx)
        if c1 == num_types_defs and c2 == num_types_defs:
            off1 = va_to_off(p1)
            off2 = va_to_off(p2)
            if off1 > 0 and off2 > 0:
                field_offsets_table_off = off1
                break
    pos = idx + 8

print("=== 1. Nested Types around StreamedListView (5788..5800) & Header (5950..5955) & VirtualisedList ===")
_, m_cnt_mod, m_ptrs_va = modules["SI.Bindable.dll"]
ptrs_off = va_to_off(m_ptrs_va)
for ti in list(range(5785, 5805)) + [5950, 5951]:
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    f_start, f_cnt = tu[8], tu[17] & 0xFFFF
    m_start, m_cnt = tu[9], tu[16] & 0xFFFF
    arr_va = struct.unpack_from("<Q", pe, field_offsets_table_off + ti * 8)[0]
    foff_arr_off = va_to_off(arr_va) if arr_va > 0 else -1
    print(f"\n--- Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
    for fi in range(f_start, f_start + f_cnt):
        fu = struct.unpack_from("<3i", meta, real_fields_off + fi * 12)
        fname = get_mstr(fu[0])
        foff_val = struct.unpack_from("<I", pe, foff_arr_off + (fi - f_start) * 4)[0] if foff_arr_off > 0 else -1
        print(f"  Field {fi - f_start:2d} (+0x{foff_val:03x}): {fname}")
    if ti != 5791:
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rid = (mu[6] & 0xFFFFFF) - 1
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
            rva = va - image_base if va else 0
            print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")

# Also find VirtualisedList type index
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if "Virtualised" in tname or "Sort" in tname or "Header" in tname:
                f_start, f_cnt = tu[8], tu[17] & 0xFFFF
                m_start, m_cnt = tu[9], tu[16] & 0xFFFF
                arr_va = struct.unpack_from("<Q", pe, field_offsets_table_off + ti * 8)[0]
                foff_arr_off = va_to_off(arr_va) if arr_va > 0 else -1
                print(f"\n--- Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
                for fi in range(f_start, f_start + f_cnt):
                    fu = struct.unpack_from("<3i", meta, real_fields_off + fi * 12)
                    fname = get_mstr(fu[0])
                    foff_val = struct.unpack_from("<I", pe, foff_arr_off + (fi - f_start) * 4)[0] if foff_arr_off > 0 else -1
                    print(f"  Field {fi - f_start:2d} (+0x{foff_val:03x}): {fname}")
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    rid = (mu[6] & 0xFFFFFF) - 1
                    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                    rva = va - image_base if va else 0
                    print(f"  Method idx={mi} ({mname}): RVA=0x{rva:08x}")

print("\n=== 2. StreamedTable/UxmlSerializedData in Recruitment Assets (229, 263, 177, 111, 103) ===")
raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees_r["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]
for oi in (229, 263, 177, 111, 103):
    _, pid, abs_off, bsize, tid = objs_r[oi]
    chunk = raw_r[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    pat = b"StreamedTable/UxmlSerializedData"
    idx = chunk.find(pat)
    print(f"\n==================== Obj {oi} ({name}) idx={idx} ====================")
    if idx != -1:
        p = idx + 64
        for c in top_children:
            cname = st_nodes[c][3]
            try:
                p_next, val = walk_tree(st_nodes, chunk, p, c)
                if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                    print(f"  +0x{p - (idx+64):03x} {cname}: {val}")
                p = p_next
            except Exception as e:
                print(f"  ERROR at {cname} (+0x{p - (idx+64):03x}): {e}")
                break

print("\n=== 3. Disassembly of StreamedListView Sorting & Header Methods ===")
disasm_targets = [
    ("Header.SetupClickHandler", 0x015df7e0),
    ("Header.Bind", 0x015df4f0),
    ("Header.UpdateSortingIcons", 0x015df970),
    ("Header.ResetSortingIcons", 0x015df720),
    ("Header.OnBindingChanged", 0x015df600),
    ("StreamedTable.<MakeColumnHeader>b__0", 0x0160bb80),
    ("StreamedListView.get_ReceivedAllSortingData", 0x015acd40),
    ("StreamedListView.set_Reorderable", 0x015ad4f0),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.SetSortingBinding_uint", 0x015a9a80),
    ("StreamedListView.SetSortingBinding_str", 0x015a9ae0),
    ("StreamedListView.HasSorting", 0x015a5f20),
    ("StreamedListView.ApplySorting", 0x015a4260),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850),
    ("StreamedListView.SetNoSorting", 0x015a99d0),
    ("StreamedListView.ClearSortingState", 0x015a5180),
    ("StreamedListView.OnSortBindingChanged", 0x015a7ca0),
    ("StreamedListView.OnResetSortingEvent", 0x015a7870),
    ("StreamedListView.EndStateChange", 0x015a5350),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.SetList", 0x015a9880),
    ("StreamedListView.Refresh", 0x015a9390),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedListView.Rebuild", 0x015a8eb0),
    ("StreamedListView.UxmlSerializedData.Deserialize", 0x015b0b50),
    ("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0),
]

for name, rva in disasm_targets:
    end_rva = rva_to_end.get(rva, rva + 0x100)
    dump_fast(name, rva, end_rva)

out_file.flush()
out_file.close()
