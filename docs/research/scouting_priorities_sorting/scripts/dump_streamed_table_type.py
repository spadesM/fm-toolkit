import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()
hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[24], hdr[25]
types_off, types_sz = hdr[40], hdr[41]

def get_mstr(off):
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if tname in ("StreamedTable", "StreamedListView", "StreamedObjectList"):
        print(f"\n================ TYPE {ti}: {tns}.{tname} ================")
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        print(f"Fields ({f_cnt}):")
        for fi in range(f_start, f_start + f_cnt):
            fn_idx, ft_idx, f_tok = struct.unpack_from("<iiI", meta, fields_off + fi * 12)
            print(f"  Field {fi - f_start}: {get_mstr(fn_idx)} (type_idx={ft_idx})")
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"Methods ({m_cnt}):")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            print(f"  Method {mi - m_start} (idx={mi}): {get_mstr(mu[0])}")
