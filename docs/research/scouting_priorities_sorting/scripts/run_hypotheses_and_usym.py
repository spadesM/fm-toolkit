import sys
sys.stdout.reconfigure(encoding="utf-8")
from annotate_sorting_usym import dump_annotated, usym_map, root
import struct

# Also load USYM for 0x00670000..0x006b0000 and 0x00ab0000..0x00ac0000
usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
if not usym_path.exists():
    usym_path = root / "il2cpp.usym"
if usym_path.exists():
    udata = usym_path.read_bytes()
    _, _, sym_count, _, _, _ = struct.unpack_from("<4sIIIII", udata, 0)
    records_off = 24
    str_table_off = records_off + sym_count * 24
    str_blob = udata[str_table_off:]
    def get_ustr(off):
        if off <= 0 or off >= len(str_blob):
            return ""
        end = str_blob.find(b"\x00", off)
        return str_blob[off:end].decode("utf-8", errors="replace")
    for i in range(sym_count):
        rva, parent_idx, sym_off, file_off, line, flags = struct.unpack_from("<IIIIII", udata, records_off + i * 24)
        if (0x00670000 <= rva <= 0x006b0000) or (0x00ab0000 <= rva <= 0x00fd0000):
            usym_map.setdefault(rva, []).append((get_ustr(sym_off), get_ustr(file_off), line))

for name, rva in [
    ("StreamedTable.MakeColumnHeader", 0x015eac30),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.UpdateStreamedTableView", 0x015f1650),
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
    ("SpecificallyScoutedPersonReference.OpenChannel", 0x006970a0),
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360),
    ("ScoutPlayerPrioritiesReference.OpenChannel", 0x0067d400),
]:
    dump_annotated(name, rva)
