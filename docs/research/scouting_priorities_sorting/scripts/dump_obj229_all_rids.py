import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

raw, trees, objs, ref_trees = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")

# Find objects by PathID or index
pid_map = {pid: (oi, abs_off, bsize, tid) for oi, pid, abs_off, bsize, tid in objs}

for sheet_pid, label in [(7881143121539272450, "ScoutPrioritiesBlock inlineSheet"), (-8397452150629602669, "ScoutPrioritiesBlock-Small inlineSheet"), (668723260922630103, "TeamReportPriorities inlineSheet")]:
    if sheet_pid in pid_map:
        oi, abs_off, bsize, tid = pid_map[sheet_pid]
        chunk = raw[abs_off : abs_off + bsize]
        class_id, nodes = trees[tid]
        _, val = walk_tree(nodes, chunk, 0, 0)
        print(f"\n=== {label} (Obj {oi}, pid={sheet_pid}) ===")
        for k, v in val.items():
            print(f"  {k}: {v}")

# Also dump all RefIds in Obj 229 (ScoutPrioritiesBlock)
oi, pid, abs_off, bsize, tid = [x for x in objs if x[0] == 229][0]
chunk = raw[abs_off : abs_off + bsize]
# Let's scan for rid=1000..1017 in chunk
print("\n=== RefIds in ScoutPrioritiesBlock (Obj 229) ===")
for rid in range(1000, 1018):
    pat = struct.pack("<q", rid)
    pos = chunk.find(pat, 2700)
    if pos != -1:
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
        key = (cname, ns, asm)
        print(f"  rid={rid}: {ns}.{cname} ({asm}) at data_pos={pos}")
        if key in ref_trees:
            rnodes = ref_trees[key]
            try:
                _, rval = walk_tree(rnodes, chunk, pos, 0)
                # print non-empty fields
                non_empty = {k: v for k, v in rval.items() if v not in (0, "", [], {}, {'m_path': ''}, {'m_AssetGUID': '', 'm_SubObjectName': '', 'm_SubObjectType': ''}, {'m_FileID': 0, 'm_PathID': 0}) and not k.endswith("_UxmlAttributeFlags")}
                print(f"    -> {non_empty}")
            except Exception as e:
                print(f"    -> walk error: {e}")
