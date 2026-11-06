import struct
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")

end_of_str_buf = 153394
for hdr_off in range(120000, 152000):
    nn, ssz = struct.unpack_from("<II", raw, hdr_off)
    if 50 <= nn <= 1000 and hdr_off + 8 + nn * 32 + ssz == end_of_str_buf:
        print(f"Found TypeTree header at {hdr_off}: n_nodes={nn}, str_sz={ssz}")
        nodes_off = hdr_off + 8
        str_off = nodes_off + nn * 32
        str_buf = raw[str_off : str_off + ssz]
        def get_tstr(off):
            if off & 0x80000000:
                return f"common_{off & 0x7FFFFFFF}"
            end = str_buf.find(b"\x00", off)
            return str_buf[off:end].decode("ascii", errors="replace")
        for i in range(nn):
            ver, lvl, tflags, t_off, n_off, bsz, idx, mflag, rhash = struct.unpack_from("<HBBIiiiiQ", raw, nodes_off + i * 32)
            if lvl <= 2:
                print(f"{i:3d}: {'  '*lvl}{get_tstr(t_off)} {get_tstr(n_off)} (size={bsz}, mflag=0x{mflag:x})")
        break
