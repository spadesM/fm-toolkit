import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Find all methods in InteropReference.cs from il2cpp.usym
udata = dhf.udata
sym_count = dhf.sym_count
records_off = dhf.records_off

for idx in range(sym_count):
    rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + idx * 24)
    fn = dhf.get_ustr(file_off)
    if "InteropReference" in fn or "PropertyRegistration" in fn or "AutogenBindings" in fn:
        sym = dhf.get_ustr(sym_off)
        if line < 300:
            print(f"RVA=0x{rva:08x} sym={sym} file={fn}:{line}")

dhf.dump_fast("AutogenBindings_2ae590", 0x002ae590, 0x002ae700)
dhf.dump_fast("InteropReference_1692970", 0x01692800, 0x01693000)
