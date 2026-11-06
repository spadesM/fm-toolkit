import struct
from check_deep_sorting import root
from list_recruitment_objs import parse_bundle_clean, read_typetree

aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
raw, trees, objs = parse_bundle_clean(aa_dir / "ui-recruitment_assets_all.bundle")

# Find StreamedTable/UxmlSerializedData in m_RefTypes
with open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\compare_full_st_serialized_data.py") as f:
    pass

from compare_full_st_serialized_data import st_nodes, top_children

for oid, name in [(229, "ScoutPrioritiesBlock"), (263, "ScoutPrioritiesBlock-Small"), (111, "ShortlistMainBlock")]:
    for o in objs:
        if o["path_id"] == oid:
            b = raw[o["offset"]:o["offset"]+o["size"]]
            marker = b"SI.Bindable.StreamedTable/UxmlSerializedData\x00"
            idx = b.find(marker)
            pos = idx + len(marker)
            if pos % 4 != 0:
                pos += 4 - (pos % 4)
            for s_str in (b"Assembly-CSharp\x00", b"FM.UI\x00"):
                if b[pos:pos+4] == struct.pack("<I", len(s_str)-1):
                    pos += 4 + len(s_str)
                    if pos % 4 != 0:
                        pos += 4 - (pos % 4)
            dstart = pos
            print(f"\n=== Obj {oid} ({name}) dstart={dstart} total_len={len(b)} rem={len(b)-dstart} ===")
            cur = dstart
            for s, e in top_children[:-1]: # exclude references
                sub = st_nodes[s:e]
                base_lvl = sub[0][0]
                adj = [(n[0]-base_lvl, n[1], n[2], n[3], n[4], n[5]) for n in sub]
                val, next_cur = read_typetree(b, cur, adj)
                rel = cur - dstart
                if rel >= 0x380 or val not in (0, "", [], {}, 0.0):
                    print(f"  +0x{rel:03x} (size={next_cur-cur:2d}) {sub[0][3]}: {val}")
                cur = next_cur
            print(f"  After fields before references: cur={cur}, len(b)={len(b)}, remaining bytes={b[cur:].hex(' ')}")
