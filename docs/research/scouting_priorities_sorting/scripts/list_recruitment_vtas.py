import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\recruitment_vtas_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from compare_full_st_serialized_data import parse_bundle_with_reftypes

raw_r, trees_r, objs_r, ref_trees_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_r:
    chunk = raw_r[abs_off : abs_off + bsize]
    tname, nodes = trees_r[tid]
    if tname == "VisualTreeAsset":
        slen = struct.unpack_from("<I", chunk, 0)[0]
        nm = chunk[4 : 4 + slen].decode("utf-8", errors="replace")
        print(f"Obj {oi:3d}: pid={pid:20d} size={bsize:6d} name={nm}")

out_file.close()
