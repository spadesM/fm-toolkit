import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import resolve_data_rva
from check_deep_sorting import pe, image_base, off_to_va
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# A. Decode the 7 property names of J1Ct by looking AFTER `b9 xx xx xx xx`
prop_ids = [
    (b"\xb9\x72\x79\x6c\x70", "J1Ct:plyr (0x706c7972)"),
    (b"\xb9\x61\x78\x4d\x64", "J1Ct:axMd (0x644d7861)"),
    (b"\xb9\x45\x45\x59\x63", "J1Ct:EEYc (0x63594545)"),
    (b"\xb9\x33\x63\x44\x75", "J1Ct:3cDu (0x75446333)"),
    (b"\xb9\x76\x4c\x75\x71", "J1Ct:vLuq (0x71754c76)"),
    (b"\xb9\x20\x4e\x71\x73", "J1Ct:_Nqs (0x73714e20)"),
    (b"\xb9\x73\x57\x47\x6e", "J1Ct:sWGn (0x6e475773)"),
    (b"\xb9\x47\x20\x69\x72", "ao3d:ri_G (0x72692047)"),
    (b"\xb9\x49\x36\x39\x67", "ao3d:g96I (0x67393649)"),
    (b"\xb9\x32\x32\x6a\x73", "ao3d:sj22 (0x736a3232)"),
    (b"\xb9\x43\x50\x73\x73", "ao3d:ssPC (0x73735043)"),
]

print("=== A. Exact Property Names of J1Ct and ao3d ===")
for pat, label in prop_ids:
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003e4f30 <= rva <= 0x004c5d06:
            # Look FORWARD 0..80 bytes for 4c 8b 05 (mov r8, [rip + disp])
            chunk = pe[idx : idx + 88]
            for i in range(len(chunk) - 7):
                if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
                    disp = struct.unpack_from("<i", chunk, i + 3)[0]
                    insn_rva = rva + i
                    trva = insn_rva + 7 + disp
                    print(f"  {label:28s} at RVA 0x{rva:08x} -> {resolve_data_rva(trva)}")
                    break
        pos = idx + 1

# B. Compare full RowData dicts in SpecificallyScoutedPersonTableFactory (Obj 92) vs PlayerTableFactory (Obj 31) vs PrioritiseFutureTransferItemTableFactory (Obj 118)
print("\n=== B. RowData Comparison in ui-tablefactories_assets_all.bundle ===")
raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi in (92, 118, 31):
    _, pid, abs_off, bsize, tid = objs_f[oi]
    _, nodes = trees_f[tid]
    chunk = raw_f[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- Factory Obj {oi}: {val.get('common_436')} ---")
    for r in val.get("m_rowData", [])[:10]:
        print(" ", r)

# C. Compare ScoutPrioritiesTable (Obj 766) with other tables in ui-tableviews_assets_all.bundle
print("\n=== C. TableView Comparison in ui-tableviews_assets_all.bundle ===")
raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi, (_, pid, abs_off, bsize, tid) in enumerate(objs_v):
    if not (0 <= tid < len(trees_v)):
        continue
    _, nodes = trees_v[tid]
    chunk = raw_v[abs_off : abs_off + bsize]
    if bsize < 36:
        continue
    ln = struct.unpack_from("<I", chunk, 28)[0]
    name = chunk[32 : 32 + ln].decode("utf-8", errors="replace") if 32 + ln <= len(chunk) else ""
    if oi == 766 or "ScoutPriorit" in name or "Shortlist" in name or "Recommendations" in name:
        try:
            _, val = walk_tree(nodes, chunk, 0, 0)
            if "m_tableConfig" in val:
                print(f"\n--- TableView Obj {oi}: {name} (pid={pid}) ---")
                for k, v in val.items():
                    if k != "m_tableConfig":
                        print(f"  {k}: {v}")
                for col in val["m_tableConfig"][:12]:
                    print(f"  col: {col}")
        except Exception as e:
            print(f"  Obj {oi} {name} err: {e}")
