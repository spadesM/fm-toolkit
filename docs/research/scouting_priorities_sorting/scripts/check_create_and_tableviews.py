import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_j1ct_and_nth_prop import resolve_data_rva, dump_with_strings
from check_deep_sorting import pe, image_base, off_to_va
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Dump Bindings.Create (0x014bf980) and its callees!
dump_with_strings("Bindings.Create", 0x014bf980)

# 2. Exact Property Names of J1Ct and ao3d (looking forward 0..120 bytes)
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

print("\n=== Exact Property Names of J1Ct and ao3d ===")
for pat, label in prop_ids:
    pos = 0
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        rva = off_to_va(idx) - image_base
        if 0x003e4f30 <= rva <= 0x004c5d06:
            chunk = pe[idx : idx + 120]
            for i in range(len(chunk) - 7):
                if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
                    disp = struct.unpack_from("<i", chunk, i + 3)[0]
                    insn_rva = rva + i
                    trva = insn_rva + 7 + disp
                    print(f"  {label:28s} at RVA 0x{rva:08x} -> {resolve_data_rva(trva)}")
                    break
        pos = idx + 1

# 3. Dump ScoutPrioritiesBlock.uxml (Obj 229) and RecruitmentScoutPrioritiesCard.uxml (Obj 177) full UXML tree in ui-recruitment_assets_all.bundle
print("\n=== UXML Hierarchy of Obj 177 and Obj 229 in ui-recruitment_assets_all.bundle ===")
raw_r, trees_r, objs_r, ref_r = parse_bundle_with_reftypes("ui-recruitment_assets_all.bundle")
for oi in (177, 229, 263):
    _, pid, abs_off, bsize, tid = objs_r[oi]
    _, nodes = trees_r[tid]
    chunk = raw_r[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- UXML Obj {oi}: {val.get('common_436')} ---")
    for vea in val.get("m_VisualElementAssets", []):
        print(f"  VEA id={vea.get('m_Id')} parent={vea.get('m_ParentId')} type={vea.get('m_FullTypeName')} classes={vea.get('m_Classes')} props={vea.get('m_Properties')}")
    for ta in val.get("m_TemplateAssets", []):
        print(f"  TA  id={ta.get('m_Id')} parent={ta.get('m_ParentId')} template={ta.get('m_TemplateAlias')} props={ta.get('m_Properties')} attrOverrides={ta.get('m_AttributeOverrides')}")
