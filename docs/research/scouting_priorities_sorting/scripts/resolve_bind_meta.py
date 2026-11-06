import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

meta = dhf.meta
hdr = dhf.hdr
types_off, types_sz = dhf.types_off, dhf.types_sz
methods_off, methods_sz = dhf.methods_off, dhf.methods_sz
fields_off = hdr[24]

print("=== StreamedListView & StreamedTable Fields ===")
for tidx in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + tidx * 88)
    tname = dhf.get_mstr(tu[0])
    if tname in ("StreamedListView", "StreamedTable"):
        fstart = tu[9]
        fcount = (tu[17] >> 16) & 0xFFFF
        print(f"\nType {tidx}: {dhf.get_mstr(tu[1])}.{tname} (fields={fcount}, fstart={fstart})")
        for fi in range(fstart, fstart + fcount):
            fname_off, ftype_idx, ftok = struct.unpack_from("<iii", meta, fields_off + fi * 12)
            print(f"  Field {fi - fstart}: {dhf.get_mstr(fname_off)}")

print("\n=== Disassemble 0x00e6dcf0, 0x014c1c20, 0x014c5650, StreamedListView_0x015a5680, StreamedTable_0x015acdf0 ===")
dhf.dump_fast("Method_0x00e6dcf0", 0x00e6dcf0, 0x00e6de00)
dhf.dump_fast("Bindings_0x014c1c20 (Bindings.cs:2134)", 0x014c1c20, 0x014c1d40)
dhf.dump_fast("Bindings_0x014c5650 (Bindings.cs:1933)", 0x014c5650, 0x014c5950)
dhf.dump_fast("StreamedListView_0x015a5680 (StreamedListView.cs:1571)", 0x015a5680, 0x015a5a10)
dhf.dump_fast("StreamedTable_0x015acdf0 (StreamedListView.cs:404)", 0x015acdf0, 0x015ace50)
