import struct
from dump_table_factory_methods import dump_clean, pe, meta, image_base, va_to_off, get_mstr, methods_off, types_off, methods_sz, types_sz, hdr

# Search for types with "TableFactory" or "ColumnFactory" in their name
for tidx in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + tidx * 88)
    tname = get_mstr(tu[0])
    if "TableFactory" in tname or "ColumnFactory" in tname or "ColumnConfig" in tname or "TableView" in tname:
        m_start = tu[8]
        m_cnt = tu[15] & 0xFFFF
        print(f"Type {tidx}: {get_mstr(tu[1])}.{tname} (methods={m_cnt})")
        if m_start >= 0 and m_cnt < 500:
            for mi in range(m_start, m_start + m_cnt):
                if 0 <= mi * 36 < methods_sz:
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    print(f"  Method {mi}: {get_mstr(mu[0])} (token=0x{mu[6]&0xffffffff:08x})")

dump_clean("StreamedTable.MakeColumnHeader", 0x015eac30, 800)
