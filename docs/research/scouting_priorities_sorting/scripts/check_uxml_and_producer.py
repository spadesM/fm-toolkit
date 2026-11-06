import struct, sys

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\uxml_and_producer_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

print("=== 1. Dump StreamedTable/UxmlSerializedData in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees_r["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

for oi in (177, 229, 263, 360, 111, 103):
    _, pid, abs_off, bsize, tid = objs_r[oi]
    chunk = raw_r[abs_off : abs_off + bsize]
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace")
    print(f"\n==================== Obj {oi} ({name}, pid={pid}, size={bsize}) ====================")
    # Find all strings in chunk to see all bindings and classes
    pat = b"StreamedTable/UxmlSerializedData"
    pos_s = 0
    while True:
        idx = chunk.find(pat, pos_s)
        if idx == -1:
            break
        p = idx + 64
        print(f"  [StreamedTable at dstart={p}]")
        dstart = p
        for c in top_children:
            cname = st_nodes[c][3]
            try:
                p_next, val = walk_tree(st_nodes, chunk, p, c)
                if val not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                    print(f"    +0x{p - dstart:03x} {cname}: {val}")
                p = p_next
            except Exception as e:
                print(f"    ERROR at {cname} (+0x{p - dstart:03x}): {e}")
                break
        pos_s = idx + 1

print("\n=== 2. Search GameAssembly.dll for SpecificallyScoutedPerson ID 0x7443314a (4a 31 43 74) ===")
pos = 0
while True:
    idx = pe.find(b"\x4a\x31\x43\x74", pos)
    if idx == -1:
        break
    va = off_to_va(idx)
    if va > 0:
        rva = va - image_base
        fn_rva = max((k for k in rva_to_end if k <= rva and rva < rva_to_end[k]), default=0)
        print(f"Found 0x7443314a at file_off=0x{idx:x} RVA=0x{rva:08x} in {rva_to_method_name.get(fn_rva)} (0x{fn_rva:08x})")
        if fn_rva > 0 and fn_rva not in (0x00696ef0, 0x00696f50, 0x00696f60, 0x00697370):
            sz = min(rva_to_end.get(fn_rva, fn_rva + 800) - fn_rva, 1200)
            dump_func_details(f"Ref 0x7443314a in {rva_to_method_name.get(fn_rva)}", fn_rva, sz)
    pos = idx + 1

print("\n=== 3. Search GameAssembly.dll for SpecificallyScoutedTeam ID 0x53434c4b (4b 4c 43 53) ===")
pos = 0
while True:
    idx = pe.find(b"\x4b\x4c\x43\x53", pos)
    if idx == -1:
        break
    va = off_to_va(idx)
    if va > 0:
        rva = va - image_base
        fn_rva = max((k for k in rva_to_end if k <= rva and rva < rva_to_end[k]), default=0)
        print(f"Found 0x53434c4b at file_off=0x{idx:x} RVA=0x{rva:08x} in {rva_to_method_name.get(fn_rva)} (0x{fn_rva:08x})")
        if fn_rva > 0 and fn_rva not in (0x00697370, 0x00697380, 0x006973a0, 0x006973b0, 0x00697770):
            sz = min(rva_to_end.get(fn_rva, fn_rva + 800) - fn_rva, 1200)
            dump_func_details(f"Ref 0x53434c4b in {rva_to_method_name.get(fn_rva)}", fn_rva, sz)
    pos = idx + 1

out_file.close()
