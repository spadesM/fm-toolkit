import struct, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
fields_off, fields_sz = hdr[24], hdr[25]
types_off, types_sz = hdr[40], hdr[41]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

# Print fields of Type 5791 (StreamedListView) and Type 5967 (StreamedTable)
for ti in [5791, 5951, 5967]:
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    f_start = tu[8]
    f_cnt = tu[17] & 0xFFFF
    print(f"=== Type {ti}: {tname} (fields={f_cnt}, start={f_start}) ===")
    for fi in range(f_start, f_start + f_cnt):
        fu = struct.unpack_from("<2i", meta, fields_off + fi * 12)
        fname = get_mstr(fu[0])
        print(f"  [{fi - f_start:2d}] {fname}")
