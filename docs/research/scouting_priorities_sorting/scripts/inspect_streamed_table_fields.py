import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, get_mstr, types_off, types_sz, fields_off, fields_sz, methods_off, methods_sz, images_off, images_sz, modules

# Find Il2CppTypeDefinition field offsets from GameAssembly.dll typeInfoPointers or TypeDefinition field_start
# Let's locate Il2CppMetadataRegistration in GameAssembly.dll to get fieldOffsets table!
# In IL2CPP, fieldOffsets is an array of int32[] or uint32* indexed by typeIndex or flat field index.
# Let's find the type definitions for VirtualisedList, StreamedListView, StreamedTable, Header, Column
target_types = {"VirtualisedList", "StreamedListView", "StreamedTable", "Header", "Column"}

for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname not in ("SI.Bindable.dll", "FM.UI.dll"):
        continue
    t_start, t_cnt = iu[2], iu[3]
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        if tname in target_types:
            f_start = tu[8]
            f_cnt = tu[17] & 0xFFFF
            print(f"\n=== Type {ti}: {iname} :: {tname} (fields={f_cnt}, field_start={f_start}) ===")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                fname = get_mstr(fu[0])
                print(f"  Field {fi - f_start} (global {fi}): {fname}")
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            _, m_cnt_mod, m_ptrs_va = modules[iname]
            ptrs_off = va_to_off(m_ptrs_va)
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if 0 <= rid < m_cnt_mod else 0
                rva = va - image_base if va else 0
                print(f"  Method {mname}: RVA=0x{rva:08x}")
