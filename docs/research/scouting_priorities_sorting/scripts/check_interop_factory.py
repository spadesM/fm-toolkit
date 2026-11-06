import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, types_sz, methods_off, images_off, images_sz, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

dump_func_details("InteropUtils.TryCreateReference", 0x01692da0)
dump_annotated("InteropUtils.TryCreateReference", 0x01692da0)

dump_func_details("InteropListExtensions.TryGetValue", 0x016925d0)
dump_annotated("InteropListExtensions.TryGetValue", 0x016925d0)

# Find all types with "Factory" or "Interop" or "Reference" in FM.UI or SI.Bindable
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    nspace = get_mstr(tu[1])
    if "Interop" in tname or "ReferenceFactory" in tname or "ReferenceRegistration" in tname or "PropertyRegistration" in tname:
        print(f"Type {ti}: {nspace}.{tname} (parent={tu[4]}, methods={tu[16]&0xFFFF})")
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            print(f"  [{mi}] {get_mstr(mu[0])} (token=0x{mu[6]:08x})")
