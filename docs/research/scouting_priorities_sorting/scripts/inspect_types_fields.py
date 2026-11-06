import struct, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()
hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[22], hdr[23]
types_off, types_sz = hdr[40], hdr[41]

def get_mstr(off):
    if off < 0 or off >= str_sz: return ""
    return meta[str_off + off : meta.find(b"\x00", str_off + off)].decode("utf-8", errors="replace")

def get_type_info(tidx):
    if 0 <= tidx * 88 < types_sz:
        tu = struct.unpack_from("<22i", meta, types_off + tidx * 88)
        return f"{get_mstr(tu[1])}.{get_mstr(tu[0])}", tu
    return f"Type#{tidx}", None

# Check StreamedTable and StreamedTable.UxmlSerializedData and StreamedListView fields
num_types = types_sz // 88
for tidx in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + tidx * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if tname in ("StreamedTable", "StreamedListView", "UxmlSerializedData", "SpecificallyScoutedPerson", "SpecificallyScoutedPlayer", "ScoutPriorities", "CurrentScoutingPrioritiesList") or "ScoutPriorit" in tname or "SpecificallyScouted" in tname:
        parent_name = ""
        if tu[3] >= 0:
            parent_name = f"parent_byval={tu[3]}"
        first_f, f_cnt = tu[8], tu[17] & 0xFFFF
        if tname == "UxmlSerializedData" and f_cnt < 15:
            continue
        print(f"\n=== Type[{tidx}] {tns}.{tname} (fields={f_cnt}, methods={tu[16]&0xFFFF}) ===")
        for fi in range(first_f, first_f + f_cnt):
            if 0 <= fi * 12 < fields_sz:
                fn_off, ft_idx = struct.unpack_from("<ii", meta, fields_off + fi * 12)[:2]
                print(f"  field[{fi - first_f}] {get_mstr(fn_off)} (type_byval={ft_idx})")
        first_m, m_cnt = tu[7], tu[16] & 0xFFFF
        if "Scout" in tname or "Specifically" in tname:
            for mi in range(first_m, first_m + m_cnt):
                if 0 <= mi * 36 < methods_sz:
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    print(f"  method[{mi}] {get_mstr(mu[0])}")
