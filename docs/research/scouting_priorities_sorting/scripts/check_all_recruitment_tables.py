import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
st_nodes = ref_trees["StreamedTable/UxmlSerializedData"]
top_children = [i for i, n in enumerate(st_nodes) if n[0] == 1]

print("=== ALL StreamedTable in ui-recruitment_assets_all.bundle ===")
pat = b"StreamedTable/UxmlSerializedData"
for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    if pat in chunk:
        _, nodes = trees[tid]
        try:
            _, val = walk_tree(nodes, chunk, 0, 0)
            name = val.get("m_Name", f"obj_{oi}")
        except Exception:
            ln = struct.unpack_from("<I", chunk, 28)[0] if bsize >= 32 else 0
            name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 0 < ln < 200 else f"obj_{oi}"
        pos = 0
        occ = 0
        while True:
            idx = chunk.find(pat, pos)
            if idx == -1:
                break
            occ += 1
            p = idx + 64
            print(f"\n--- Obj {oi} (pid={pid}, {name}) occ #{occ} ---")
            for c in top_children:
                cname = st_nodes[c][3]
                try:
                    p_next, v = walk_tree(st_nodes, chunk, p, c)
                    if v not in (0, 0.0, "", [], {}, {"m_path": ""}, {"GameID": 0}, {"m_AssetGUID": "", "m_SubObjectName": "", "m_SubObjectType": ""}, {"m_FileID": 0, "m_PathID": 0}, 2):
                        print(f"  +0x{p - (idx+64):03x} {cname}: {v}")
                    p = p_next
                except Exception as e:
                    print(f"  ERROR at {cname}: {e}")
                    break
            pos = idx + len(pat)

print("\n=== Other Priorit / Scout objects in ui-recruitment_assets_all.bundle ===")
for oi, pid, abs_off, bsize, tid in objs:
    chunk = raw[abs_off : abs_off + bsize]
    _, nodes = trees[tid]
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
        name = val.get("m_Name", "") if isinstance(val, dict) else ""
        if any(k in name.lower() for k in ("priorit", "specifically", "focus", "shortlist", "recommend")):
            print(f"Obj {oi} (pid={pid}, tid={tid}): {name} -> keys={list(val.keys())}")
            if "m_tableConfig" in val or "m_views" in val or "m_tableViews" in val or "m_defaultView" in val:
                print(f"   FULL: {val}")
    except Exception:
        pass
