import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, fields_off, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# Let's check interfaces, fields, and vtable of Type 909 (SpecificallyScoutedPersonReference) vs Type 860 (ScoutPlayerPrioritiesReference) vs Type 17606 (InteropReference)
ifaces_off, ifaces_sz = hdr[32], hdr[33] # wait: let's check hdr for interfacesOffset and vtableMethodsOffset

# Print all *Reference types in FM.UI grouped by parent (tu[4]) and method count:
ref_by_parent = {}
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    nspace = get_mstr(tu[1])
    if nspace == "FM.UI" and tname.endswith("Reference"):
        ref_by_parent.setdefault(tu[4], []).append((ti, tname, tu[16]&0xFFFF, tu[8])) # tu[8] is fieldStart, tu[17]&0xFFFF is field_count

for p, lst in ref_by_parent.items():
    print(f"\nParent {p}: {len(lst)} FM.UI.*Reference types")
    for item in lst[:15]:
        print(" ", item)

# Also dump all methods of SI.Interop.InteropReference (Type 17606)
tu = struct.unpack_from("<22i", meta, types_off + 17606 * 88)
m_start = tu[9]
m_cnt = tu[16] & 0xFFFF
_, m_cnt_mod, m_ptrs_va = modules["SI.Interop.dll"]
ptrs_off = va_to_off(m_ptrs_va)
for mi in range(m_start, m_start + m_cnt):
    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
    mname = get_mstr(mu[0])
    rid = (mu[6] & 0xFFFFFF) - 1
    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
    rva = va - image_base if va else 0
    dump_func_details(f"InteropReference.{mname}", rva)
    dump_annotated(f"InteropReference.{mname}", rva)
