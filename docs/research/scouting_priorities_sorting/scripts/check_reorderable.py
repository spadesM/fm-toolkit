import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

# Find all methods in SI.Bindable.dll with Reorder or Drag or Sort in name
meta = cds.meta
for img_i in range(cds.images_sz // 40):
    iu = struct.unpack_from("<10i", meta, cds.images_off + img_i * 40)
    iname = cds.get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = cds.modules[iname]
        ptrs_off = cds.va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, cds.types_off + ti * 88)
            tname = cds.get_mstr(tu[0])
            if tname in ("StreamedListView", "StreamedTable", "VirtualisedList", "StreamedObjectList"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, cds.methods_off + mi * 36)
                    mname = cds.get_mstr(mu[0])
                    if any(w in mname for w in ("Reorder", "Drag", "Sort", "Header")):
                        rid = (mu[6] & 0xFFFFFF) - 1
                        va = struct.unpack_from("<Q", cds.pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                        rva = va - cds.image_base if va else 0
                        end_rva = cds.rva_to_end.get(rva, rva + 64)
                        print(f"  {tname}.{mname}: RVA=0x{rva:08x}..0x{end_rva:08x} (sz={end_rva - rva})")
                        if any(w in mname for w in ("Reorder", "Drag")):
                            dhf.dump_fast(f"{tname}.{mname}", rva, end_rva)
