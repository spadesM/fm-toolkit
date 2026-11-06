import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Search il2cpp.usym for any symbol or file matching keywords
udata = dhf.udata
sym_count = dhf.sym_count
records_off = dhf.records_off

keywords = ["SpecificallyScouted", "ScoutPriorit", "Reorder", "DragCell"]
for idx in range(sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    sym = dhf.get_ustr(sym_off)
    fn = dhf.get_ustr(file_off)
    for kw in keywords:
        if kw.lower() in sym.lower() or kw.lower() in fn.lower():
            print(f"RVA=0x{rva:08x} sym={sym} file={fn}:{line}")
            break
