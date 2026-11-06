import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, meta, rva_to_end, methods_off, types_off, get_mstr, va_to_off, image_base, dump_func_details

print("=== DONE IMPORTING ===")
# Let's list all methods of Type 5789 (StreamedListView) and Type 5874 (StreamedTable) and their UxmlSerializedData types
for ti in range(5780, 5890):
    t_off = types_off + ti * 56
    name_idx = struct.unpack_from('<I', meta, t_off)[0]
    tname = get_mstr(name_idx)
    m_start, m_count = struct.unpack_from('<II', meta, t_off + 32)[:2]
    if any(k in tname for k in ['StreamedListView', 'StreamedTable', 'UxmlSerializedData', 'Header']):
        print(f"\n=== Type {ti}: {tname} (methods={m_count}) ===")
        for mi in range(m_start, m_start + m_count):
            m_off = methods_off + mi * 32
            m_name_idx, _, m_rva = struct.unpack_from('<III', meta, m_off)[:3]
            mname = get_mstr(m_name_idx)
            if any(k in mname.lower() for k in ['reord', 'sort', 'drag', 'deserialize', 'header', 'click', 'bind', 'make', 'state']):
                print(f"  Method {mi} ({mname}): RVA=0x{m_rva:08x}")
