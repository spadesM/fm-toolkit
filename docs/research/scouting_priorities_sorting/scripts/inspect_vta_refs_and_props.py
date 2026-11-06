import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, hdr, va_to_off, off_to_va, image_base, root
)
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree

raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")
data_offset = struct.unpack_from(">Q", raw, 32)[0]
pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
trees = []
for ti in range(type_count):
    class_id = struct.unpack_from("<i", raw, pos)[0]
    script_type_index = struct.unpack_from("<h", raw, pos + 5)[0]
    pos += 7
    if class_id == 114 or script_type_index >= 0:
        pos += 16
    pos += 16
    nn, ssz = struct.unpack_from("<II", raw, pos)
    pos += 8
    nodes_off = pos
    pos += nn * 32
    str_buf = raw[pos : pos + ssz]
    pos += ssz
    def get_tstr(off, sb=str_buf):
        if off & 0x80000000:
            return f"common_{off & 0x7FFFFFFF}"
        e = sb.find(b"\x00", off)
        return sb[off:e].decode("ascii", errors="replace")
    nodes = []
    for i in range(nn):
        ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, nodes_off + i * 32)
        nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))
    dep_cnt = struct.unpack_from("<i", raw, pos)[0]
    pos += 4 + dep_cnt * 4
    trees.append((class_id, nodes))

obj_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
objs = []
for i in range(obj_count):
    pos = (pos + 3) & ~3
    pid, bstart, bsize, tid = struct.unpack_from("<qQII", raw, pos)
    pos += 24
    objs.append((i, pid, data_offset + bstart, bsize, tid))

def dump_vta_refs(obj_idx):
    oi, pid, abs_off, bsize, tid = objs[obj_idx]
    _, nodes = trees[tid]
    p = abs_off
    top_children = [i for i, n in enumerate(nodes) if n[0] == 1]
    res = {}
    for c in top_children:
        cname = nodes[c][3]
        if cname == "references":
            break
        p, val = walk_tree(nodes, raw, p, c)
        res[cname] = val
    ver = struct.unpack_from("<i", raw, p)[0]
    ref_cnt = struct.unpack_from("<i", raw, p + 4)[0]
    print(f"\n=== Obj {obj_idx} ({res.get('common_427')}) RefIds (ver={ver}, count={ref_cnt}) ===")
    # Scan for "/UxmlSerializedData" in raw[p : abs_off + bsize]
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
                    headers.append((scan, c3, rid, cls_s, ns_s, asm_s))
            except Exception:
                pass
    for idx, (h_start, data_start, rid, cls_s, ns_s, asm_s) in enumerate(headers):
        data_end = headers[idx + 1][0] if idx + 1 < len(headers) else end_off
        dbytes = raw[data_start:data_end]
        strs = []
        for sp in range(0, len(dbytes) - 4, 4):
            slen = struct.unpack_from("<I", dbytes, sp)[0]
            if 1 <= slen <= 200 and sp + 4 + slen <= len(dbytes):
                s = dbytes[sp + 4 : sp + 4 + slen]
                pad = (4 - (slen % 4)) % 4
                if sp + 4 + slen + pad <= len(dbytes) and dbytes[sp + 4 + slen : sp + 4 + slen + pad] == b"\x00" * pad:
                    if all(32 <= b < 127 for b in s):
                        strs.append(f"+0x{sp:03x}:{s.decode('ascii')!r}")
        print(f"  rid={rid}: {cls_s} (data_len={len(dbytes)}) -> {', '.join(strs)}")

if __name__ == "__main__":
    for target_oi in (229, 263, 111, 297, 360):
        dump_vta_refs(target_oi)

    sl_off, sl_sz = hdr[2], hdr[3]
    sld_off, sld_sz = hdr[4], hdr[5]
    print(f"\nstringLiterals count = {sl_sz // 8}")
    idx = meta.find(b"SpecificallyScoutedPlayers", sld_off, sld_off + sld_sz)
    if idx != -1:
        rel = idx - sld_off
        print(f"Found SpecificallyScoutedPlayers at sld+{rel}")
    start_s = max(sld_off, idx - 500)
    end_s = min(sld_off + sld_sz, idx + 1500)
    for sl_i in range(sl_sz // 8):
        length, d_idx = struct.unpack_from("<II", meta, sl_off + sl_i * 8)
        if start_s <= sld_off + d_idx < end_s:
            s = meta[sld_off + d_idx : sld_off + d_idx + length].decode("utf-8", errors="replace")
            print(f"  SL[{sl_i}]: {s!r}")
