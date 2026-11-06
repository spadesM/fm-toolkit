import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import dump_func_details, meta, types_off, methods_off, fields_off, images_off, images_sz, get_mstr, modules, va_to_off, pe, image_base, rva_to_end, rva_to_method_name

# 1. Inspect TypeIndex 39705 (and find which image it belongs to)
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    if t_start <= 39705 < t_start + t_cnt:
        print(f"Type 39705 is in image: {iname}")
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(39700, 39715):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            ns = get_mstr(tu[1])
            f_start, m_start = tu[8], tu[9]
            m_cnt = tu[16] & 0xFFFF
            f_cnt = tu[17] & 0xFFFF
            print(f"=== Type {ti}: {ns}.{tname} (fields={f_cnt}, methods={m_cnt}) ===")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<2i", meta, fields_off + fi * 12)
                print(f"  Field {fi - f_start}: {get_mstr(fu[0])}")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                sz = rva_to_end.get(rva, rva + 64) - rva if rva else 0
                print(f"  Method {mi} ({mname}): RVA=0x{rva:08x} size={sz}")

# 2. Also dump StreamedTable.BindToDataInternal, OnFactoryAssetLoaded, CreateColumns, CreateColumn
for name, rva, sz in [
    ("StreamedTable.CreateColumnsFromTableViewCollection", 0x015e82c0, 132),
    ("StreamedTable.CreateColumns", 0x015e83b0, 541),
    ("StreamedTable.CreateColumn", 0x015e7dc0, 942),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640, 713),
    ("StreamedTable.BindToDataInternal", 0x015e6d70, 2051),
]:
    dump_func_details(name, rva, sz)
