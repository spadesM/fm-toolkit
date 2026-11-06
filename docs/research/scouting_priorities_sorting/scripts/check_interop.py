import struct, os
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, images_off, images_sz, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname in ("SI.Interop.dll", "SI.Bindable.Reference.Core.dll"):
        print(f"\n=== Image: {iname} ===")
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            nspace = get_mstr(tu[1])
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"  Type {ti}: {nspace}.{tname} (parent={tu[4]}, methods={m_cnt})")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (0 <= rid < m_cnt_mod and ptrs_off >= 0) else 0
                rva = va - image_base if va else 0
                print(f"    [{mi}] {mname} (RVA=0x{rva:08x})")

# Also check files in root and fm_Data/Plugins for '22js' (32 32 6a 73) or 'plyr' (72 79 6c 70)
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith((".dll", ".exe")):
            fpath = os.path.join(dirpath, fn)
            try:
                data = open(fpath, "rb").read()
                c1 = data.count(b"22js")
                c2 = data.count(b"J1Ct")
                c3 = data.count(b"wy4A")
                if c1 or c2 or c3:
                    print(f"Binary {fpath}: 22js={c1}, J1Ct={c2}, wy4A={c3}")
            except Exception as e:
                pass
