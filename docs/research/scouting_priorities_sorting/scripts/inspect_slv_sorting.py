import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# Enhanced resolve_rip that also resolves TypeInfo / RuntimeTypeHandle / MethodInfo / StringLiteral
hdr = struct.unpack_from("<64I", meta, 0)
meta_usages_list_off, meta_usages_list_sz = hdr[38], hdr[39]
meta_usages_pairs_off, meta_usages_pairs_sz = hdr[36], hdr[37]

# Let's check what dhf.dump_fast prints for these functions
dhf.dump_fast("StreamedListView.ApplySorting", 0x015a4260, 0x015a4718)
dhf.dump_fast("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x015a49a6)
dhf.dump_fast("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a8ead)
dhf.dump_fast("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x015aa631)
dhf.dump_fast("SortData.HasReceived", 0x015a4040, 0x015a4260)

# Also list ALL methods of StreamedListView with their RVAs
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname != "SI.Bindable.dll":
        continue
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules[iname]
    ptrs_off = va_to_off(m_ptrs_va)
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if "StreamedListView" in tname or "Sort" in tname:
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            print(f"\n*** {iname} :: {tname} (Type {ti}, {m_cnt} methods) ***")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                print(f"  Method {mname}: RVA=0x{rva:08x}")
