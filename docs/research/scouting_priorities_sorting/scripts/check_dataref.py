import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# Check Type definitions by type index and TypeIndex (byval_arg index):
# In IL2CPP metadata, tu[4] is parentIndex (into the Type Table, i.e. Il2CppType[], not Il2CppTypeDefinition[]).
# Let's check what other types in FM.UI have tu[4]=33042 vs tu[4]=30501!
by_parent = {}
target_types = []
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    nspace = get_mstr(tu[1])
    by_parent.setdefault(tu[4], []).append((ti, f"{nspace}.{tname}", tu[16]&0xFFFF))
    if tname in ("InteropReference", "SpecificallyScoutedPersonReference", "ScoutPlayerPrioritiesReference", "DofTargetReference", "RecruitmentFocusItemReference", "PersonReference", "PlayerReference"):
        target_types.append((ti, nspace, tname, tu))

print("Count of types with parent 33042:", len(by_parent.get(33042, [])), "sample:", by_parent.get(33042, [])[:10])
print("Count of types with parent 30501:", len(by_parent.get(30501, [])), "sample:", by_parent.get(30501, [])[:10])

for ti, nspace, tname, tu in target_types:
    print(f"\n=== Type {ti}: {nspace}.{tname} (parent={tu[4]}, methods={tu[16]&0xFFFF}) ===")
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    # Find module
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        slot = mu[9]
        print(f"  method[{mi}] {mname} (slot={slot}, token=0x{mu[6]:08x})")

# Also check what Type 17606 (SI.Interop.InteropReference) methods are:
for iname, (_, m_cnt_mod, m_ptrs_va) in modules.items():
    if "Interop" in iname or "Bind" in iname or "FM.UI" in iname:
        print("Module:", iname, m_cnt_mod)
