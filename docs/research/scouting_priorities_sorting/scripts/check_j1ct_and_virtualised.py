import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, r"c:\Repos\fm26save")
from check_deep_sorting import pe, meta, hdr, types_off, types_sz, methods_off, fields_off, get_mstr, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
from annotate_sorting_usym import dump_annotated

# Find module method pointer tables
def get_mod_ptrs(dll_name):
    s_off = pe.find(b"\x00" + dll_name.encode("ascii") + b"\x00") + 1
    m_off = pe.find(struct.pack("<Q", off_to_va(s_off)))
    _, _, m_ptrs_va = struct.unpack_from("<QQQ", pe, m_off)
    return va_to_off(m_ptrs_va)

fm_ui_ptrs = get_mod_ptrs("FM.UI.dll")
si_ui_ptrs = get_mod_ptrs("SI.UI.dll")
si_bindable_ptrs = get_mod_ptrs("SI.Bindable.dll")

def dump_type_methods(ti, ptrs_off, dump_code=True):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    parent_idx = tu[3]
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"\n=== Type {ti}: {tns}.{tname} (parent={parent_idx}, methods={m_cnt}) ===")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if rid >= 0 else 0
        rva = va - image_base if va else 0
        sz = rva_to_end.get(rva, rva + 128) - rva if rva else 0
        slot = mu[9]
        print(f"  [{mi}] {mname} (slot={slot}): RVA=0x{rva:08x} (size={sz})")
        if dump_code and rva:
            dump_func_details(f"{tname}.{mname}", rva, min(sz, 0x350))
            dump_annotated(f"{tname}.{mname}", rva)

dump_type_methods(860, fm_ui_ptrs)
dump_type_methods(909, fm_ui_ptrs)

# Check parent of 909
tu909 = struct.unpack_from("<22i", meta, types_off + 909 * 88)
print("909 fields/vals:", tu909)

for i in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + i * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if tname in ("VirtualisationController", "DynamicSizeVirtualisationController", "FixedSizeVirtualisationController"):
        dump_type_methods(i, si_ui_ptrs, dump_code=True)
    elif tname in ("DataReference", "StaticDataReference", "ObjectReference") and tns == "FM.UI":
        dump_type_methods(i, fm_ui_ptrs, dump_code=True)
