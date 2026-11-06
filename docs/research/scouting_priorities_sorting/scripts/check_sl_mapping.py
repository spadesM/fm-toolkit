import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import pe, meta, hdr, va_to_off, image_base, rva_to_method_name, dump_func_details

dump_func_details("RegisterProperty_0x002a5ed0", 0x002a5ed0, 0x100)

sl_off, sl_sz = hdr[2], hdr[3]
sld_off, sld_sz = hdr[4], hdr[5]
idx = meta.find(b"SpecificallyScoutedPlayers", sld_off, sld_off + sld_sz)
start_s = max(sld_off, idx - 800)
end_s = min(sld_off + sld_sz, idx + 2500)
for sl_i in range(sl_sz // 8):
    length, d_idx = struct.unpack_from("<II", meta, sl_off + sl_i * 8)
    if start_s <= sld_off + d_idx < end_s:
        s = meta[sld_off + d_idx : sld_off + d_idx + length].decode("utf-8", errors="replace")
        print(f"  SL[{sl_i}]: {s!r}")
