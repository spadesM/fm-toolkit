import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Find all records in il2cpp.usym that mention SpecificallyScoutedPersonReference or StreamedTable.cs:100..250 or Bindings.cs
for idx in range(dhf.sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", dhf.udata, dhf.records_off + idx * 24)
    fn = dhf.get_ustr(file_off)
    sym = dhf.get_ustr(sym_off)
    if "SpecificallyScoutedPerson" in sym or "SpecificallyScoutedPerson" in fn:
        print(f"USYM idx={idx}: RVA=0x{rva:08x} sym={sym} file={fn}:{line}")
    elif "StreamedTable.cs" in fn and 100 <= line <= 165:
        print(f"USYM Header idx={idx}: RVA=0x{rva:08x} sym={sym} file={fn}:{line}")
