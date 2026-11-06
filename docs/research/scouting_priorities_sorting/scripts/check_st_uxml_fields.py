import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, image_base, rva_to_end, dump_func_details, root
)
from fm26save.binary_decompiler import unpack_unityfs_bundle

# 1. Find UxmlSerializedData for StreamedTable and StreamedListView in SI.Bindable.dll
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
        if tname in ("StreamedTable", "StreamedListView", "BindableVisualElement"):
            print(f"\n*** Type {ti}: {tname} ***")
        if tname == "UxmlSerializedData" and ti in (5790, 5957):
            f_start, f_cnt = tu[8], tu[17] & 0xFFFF
            fnames = [get_mstr(struct.unpack_from("<3i", meta, fields_off + fi * 12)[0]) for fi in range(f_start, f_start + f_cnt)]
            print(f"\n=== UxmlSerializedData (Type {ti}) ===")
            for idx, fname in enumerate(fnames):
                print(f"  Field {idx}: {fname}")
            m_start, m_cnt = tu[9], tu[16] & 0xFFFF
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                print(f"  Method {mname}: RVA=0x{rva:08x}")
                if mname == "Deserialize":
                    dump_func_details(f"Type_{ti}.UxmlSerializedData.Deserialize", rva)
