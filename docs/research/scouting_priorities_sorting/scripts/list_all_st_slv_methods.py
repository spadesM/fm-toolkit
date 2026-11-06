import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

print("=== USYM Function Map for StreamedTable.cs & StreamedListView.cs ===")
udata = dhf.udata
sym_count = dhf.sym_count
records_off = dhf.records_off
last_func = None
for idx in range(sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    if file_off == 0:
        continue
    fn = dhf.get_ustr(file_off).split("/")[-1].split("\\")[-1]
    if fn in ("StreamedTable.cs", "StreamedListView.cs", "StreamedTableView.cs", "StreamedTableFactory.cs"):
        sym = dhf.get_ustr(sym_off)
        if parent_idx != 0xFFFFFFFF and parent_idx < sym_count:
            _, _, psym_off, _, _, _ = struct.unpack_from("<IIIIII", udata, records_off + parent_idx * 24)
            psym = dhf.get_ustr(psym_off)
        else:
            psym = sym
        key = (fn, psym)
        if key != last_func:
            print(f"  0x{rva:08x}: {fn:24s}:{line:4d} -> {psym}")
            last_func = key
