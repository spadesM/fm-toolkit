import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, hdr, va_to_off, off_to_va, image_base, root
)
from inspect_vta_refs_and_props import raw, objs, trees, walk_tree

# 1. Let's hex-dump and compare the StreamedTable/UxmlSerializedData bytes for Obj 229, 263, 111, 297, 360
def get_ref_bytes(obj_idx, target_cls="StreamedTable/UxmlSerializedData"):
    oi, pid, abs_off, bsize, tid = objs[obj_idx]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {}
    for c in top_children:
        if nodes[c][3] == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[nodes[c][3]] = val
    end_off = abs_off + bsize
    headers = []
    for scan in range(p + 8, end_off - 16, 4):
        rid = struct.unpack_from("<q", raw, scan)[0]
        if rid == -2 or (1000 <= rid <= 1200):
            try:
                c1, cls_s = walk_tree(nodes, raw, scan + 8, 308)
                c2, ns_s = walk_tree(nodes, raw, c1, 312)
                c3, asm_s = walk_tree(nodes, raw, c2, 316)
                if (rid == -2 and cls_s == "" and ns_s == "" and asm_s == "") or ("/UxmlSerializedData" in cls_s):
                    headers.append((scan, c3, rid, cls_s))
            except Exception:
                pass
    for idx, (h_start, data_start, rid, cls_s) in enumerate(headers):
        data_end = headers[idx + 1][0] if idx + 1 < len(headers) else end_off
        if cls_s == target_cls:
            return res.get("common_427"), rid, raw[data_start:data_end]
    return None, None, b""

if __name__ == "__main__":
    for oi in (229, 263, 111, 297, 360):
        name, rid, dbytes = get_ref_bytes(oi)
        print(f"\n==================== Obj {oi} ({name}) StreamedTable rid={rid} len={len(dbytes)} ====================")
        p = 0
        while p < len(dbytes):
            val_u32 = struct.unpack_from("<I", dbytes, p)[0]
            if 1 <= val_u32 <= 200 and p + 4 + val_u32 <= len(dbytes):
                s = dbytes[p + 4 : p + 4 + val_u32]
                pad = (4 - (val_u32 % 4)) % 4
                if p + 4 + val_u32 + pad <= len(dbytes) and dbytes[p + 4 + val_u32 : p + 4 + val_u32 + pad] == b"\x00" * pad:
                    if all(32 <= b < 127 for b in s):
                        print(f"  +0x{p:03x}: STR ({val_u32}) {s.decode('ascii')!r}")
                        p += 4 + val_u32 + pad
                        continue
            if p + 12 <= len(dbytes):
                fid, fpid = struct.unpack_from("<iq", dbytes, p)
                if 0 <= fid <= 10 and abs(fpid) > 1000000000000:
                    print(f"  +0x{p:03x}: PPtr(fileID={fid}, pathID={fpid})")
                    p += 12
                    continue
            if val_u32 != 0:
                print(f"  +0x{p:03x}: 0x{val_u32:08x} ({val_u32})")
            p += 4
