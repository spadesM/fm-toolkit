import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, sections, rva_to_method_name, dump_func_details
)
from list_recruitment_objs import parse_bundle_clean

# 1. List all MonoBehaviours in ui-recruitment_assets_all.bundle with m_Name at abs_off + 28
raw, trees, objs = parse_bundle_clean("ui-recruitment_assets_all.bundle")
print("=== All named MonoBehaviours in ui-recruitment_assets_all.bundle ===")
for i, pid, abs_off, bsize, tid in objs:
    cid, nodes = trees[tid]
    if cid == 114 and bsize >= 32:
        ln = struct.unpack_from("<I", raw, abs_off + 28)[0]
        if 0 < ln < 200:
            name = raw[abs_off + 32 : abs_off + 32 + ln].decode("utf-8", errors="replace")
            if name != "inlineStyle":
                has_st = b"StreamedTable" in raw[abs_off : abs_off + bsize]
                has_slv = b"StreamedListView" in raw[abs_off : abs_off + bsize]
                has_tt = b"TableTemplate" in raw[abs_off : abs_off + bsize]
                flags = []
                if has_st: flags.append("StreamedTable")
                if has_slv: flags.append("StreamedListView")
                if has_tt: flags.append("TableTemplate")
                if flags or "Scout" in name or "Priorit" in name or "Recruitment" in name or "Focus" in name:
                    print(f"  Obj {i:4d} (pid={pid:20d}, sz={bsize:6d}): {name:50s} {flags}")

# 2. Search for offset 0x5c1 (c1 05 00 00) in VirtualisedList / StreamedListView / StreamedTable
print("\n=== References to +0x5c1 (m_Reorderable) in code ===")
pat = b"\xc1\x05\x00\x00"
for sname, rva_s, vsz, raw_ptr, rawsz in sections:
    if sname not in (".text", "il2cpp"):
        continue
    pos = raw_ptr
    end = raw_ptr + rawsz
    while True:
        idx = pe.find(pat, pos, end)
        if idx == -1:
            break
        hit_rva = rva_s + (idx - raw_ptr)
        best_rva = max((r for r in rva_to_method_name if r <= hit_rva), default=0)
        mnames = rva_to_method_name.get(best_rva, [])
        if any(any(k in m for k in ("VirtualisedList", "Streamed", "Table", "List", "Reorder")) for m in mnames):
            print(f"  Hit +0x5c1 at RVA 0x{hit_rva:08x} in {mnames} (0x{best_rva:08x})")
        pos = idx + 1
