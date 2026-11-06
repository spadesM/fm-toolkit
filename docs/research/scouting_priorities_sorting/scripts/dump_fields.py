import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()
hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
fields_off, fields_sz = hdr[14], hdr[15]
types_off, types_sz = hdr[40], hdr[41]

def get_mstr(off):
    if off < 0 or off >= str_sz: return ""
    return meta[str_off + off : meta.find(b"\x00", str_off + off)].decode("utf-8", errors="replace")

# Also find field offsets in GameAssembly.dll if possible, or list fields in order
for ti in (5791, 5967):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    fstart = tu[8]
    fcnt = tu[17] & 0xFFFF
    print(f"=== {tns}.{tname} (ti={ti}, fstart={fstart}, fcnt={fcnt}) ===")
    for fi in range(fstart, fstart + fcnt):
        name_idx, type_idx, token = struct.unpack_from("<iiI", meta, fields_off + fi * 12)
        print(f"  [{fi - fstart:02d}] {get_mstr(name_idx)} (type_idx={type_idx})")
