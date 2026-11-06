import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from inspect_vta_refs_and_props import raw, objs, trees, walk_tree
from parse_st_data_exact import get_ref_bytes

# Find the TypeTree for StreamedTable/UxmlSerializedData in raw!
# We know 'DisableSorting\x00' is at 0x2524f in the string buffer of StreamedTable/UxmlSerializedData's TypeTree!
# Right before the string buffer is nodes (nn * 32 bytes), and before that is (nn, ssz) = struct.unpack_from("<II", raw, pos)!
# Let's scan backwards from 0x25016 to find (nn, ssz) where pos + 8 + nn * 32 + ssz is around 0x25400!
target_str_pos = 0x25016
st_nodes = None
for scan in range(0x20000, target_str_pos, 1):
    nn, ssz = struct.unpack_from("<II", raw, scan)
    if 50 <= nn <= 500 and 500 <= ssz <= 10000:
        str_start = scan + 8 + nn * 32
        if str_start <= target_str_pos < str_start + ssz:
            # Verify first node has lvl=0
            ver, lvl = struct.unpack_from("<HB", raw, scan + 8)
            if ver in (1, 2) and lvl == 0:
                print(f"Found TypeTree at 0x{scan:x}: nn={nn}, ssz={ssz}, str_start=0x{str_start:x}")
                str_buf = raw[str_start : str_start + ssz]
                def get_tstr(off, sb=str_buf):
                    if off & 0x80000000:
                        return f"common_{off & 0x7FFFFFFF}"
                    e = sb.find(b"\x00", off)
                    return sb[off:e].decode("ascii", errors="replace")
                nodes = []
                for i in range(nn):
                    ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, scan + 8 + i * 32)
                    nodes.append((lvl, tflags, get_tstr(t_off), get_tstr(n_off), bsz, mflag))
                st_nodes = nodes
                break

if st_nodes:
    print(f"\n=== Top-level fields of StreamedTable/UxmlSerializedData (total nodes={len(st_nodes)}) ===")
    top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1 and n[3] != "references"]
    for ci in top_children:
        lvl, tflags, tname, fname, bsz, mflag = st_nodes[ci]
        print(f"  Node[{ci:3d}] {fname:<45} : {tname} (bsz={bsz}, mflag=0x{mflag:x})")

    for oi in (229, 263, 111, 297, 360):
        name, rid, dbytes = get_ref_bytes(oi)
        print(f"\n==================== Parsed Obj {oi} ({name}, len={len(dbytes)}) ====================")
        p = 0
        for ci in top_children:
            fname = st_nodes[ci][3]
            tname = st_nodes[ci][2]
            start_p = p
            p, val = walk_tree(st_nodes, dbytes, p, ci)
            if "InitFunction" in fname or "Sorting" in fname or "Sorted" in fname or "View" in fname or "Factory" in fname or "Header" in fname or "Drag" in fname or "Column" in fname or val not in (0, "", [], {}):
                print(f"  [+0x{start_p:03x}..+0x{p:03x}] {fname:<45} = {val!r}")
        print(f"  Parsed {p} / {len(dbytes)} bytes!")
