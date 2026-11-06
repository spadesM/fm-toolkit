import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root
from fm26save.binary_decompiler import unpack_unityfs_bundle
from parse_reftypes_exact import st_nodes, top_children
from inspect_vta_refs_and_props import walk_tree
from parse_st_data_exact import get_ref_bytes

top_children_valid = [ci for ci in top_children if st_nodes[ci][3] != "references"]

for oi in (229, 263, 111, 297, 360):
    name, rid, dbytes = get_ref_bytes(oi)
    print(f"\n==================== Parsed Obj {oi} ({name}, len={len(dbytes)}) ====================")
    p = 0
    for ci in top_children_valid:
        fname = st_nodes[ci][3]
        start_p = p
        p, val = walk_tree(st_nodes, dbytes, p, ci)
        if val not in (0, 0.0, "", [], {}, {'m_path': ''}, {'m_AssetGUID': '', 'm_SubObjectName': '', 'm_SubObjectType': ''}, {'m_serializedEvents': '', 'm_bytes': []}, {'m_FileID': 0, 'm_PathID': 0}):
            print(f"  [+0x{start_p:03x}..+0x{p:03x}] {fname:<45} = {val!r}")
    print(f"  Parsed {p} / {len(dbytes)} bytes!")
