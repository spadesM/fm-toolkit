import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
print("ref_trees keys sample:", list(ref_trees.keys())[:5])

def dump_all_rids(target_oi, label, start_off):
    oi, pid, abs_off, bsize, tid = [x for x in objs if x[0] == target_oi][0]
    chunk = raw[abs_off : abs_off + bsize]
    print(f"\n=== {label} (Obj {oi}) ===")
    for rid in range(1000, 1030):
        pat = struct.pack("<q", rid)
        pos = chunk.find(pat, start_off)
        if pos == -1:
            continue
        pos += 8
        clen = struct.unpack_from("<I", chunk, pos)[0]
        pos += 4
        cname = chunk[pos:pos+clen].decode("utf-8", errors="replace")
        pos = (pos + clen + 3) & ~3
        nslen = struct.unpack_from("<I", chunk, pos)[0]
        pos += 4
        ns = chunk[pos:pos+nslen].decode("utf-8", errors="replace")
        pos = (pos + nslen + 3) & ~3
        asmlen = struct.unpack_from("<I", chunk, pos)[0]
        pos += 4
        asm = chunk[pos:pos+asmlen].decode("utf-8", errors="replace")
        pos = (pos + asmlen + 3) & ~3
        # Find matching nodes in ref_trees
        rnodes = ref_trees.get((cname, ns, asm)) or ref_trees.get(cname) or ref_trees.get(f"{ns}.{cname}")
        print(f"  rid={rid}: {ns}.{cname} ({asm}) at {pos}")
        if rnodes:
            try:
                p = pos
                out = {}
                for i, n in enumerate(rnodes):
                    if n[0] == 1:
                        fn = n[3]
                        if fn == "references":
                            break
                        p, fv = walk_tree(rnodes, chunk, p, i)
                        if fv not in (0, "", [], {}, {'m_path': ''}, {'m_AssetGUID': '', 'm_SubObjectName': '', 'm_SubObjectType': ''}, {'m_FileID': 0, 'm_PathID': 0}) and not fn.endswith("_UxmlAttributeFlags"):
                            out[fn] = fv
                print(f"    -> {out}")
            except Exception as e:
                print(f"    -> err: {e}")

dump_all_rids(229, "ScoutPrioritiesBlock", 2800)
dump_all_rids(177, "RecruitmentScoutPrioritiesCard", 1360)
