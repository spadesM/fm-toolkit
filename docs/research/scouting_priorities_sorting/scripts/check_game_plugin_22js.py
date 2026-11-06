import struct, bisect
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import root, pe, meta, hdr, image_base, off_to_va, va_to_off, rva_to_method_name, rva_to_end, types_off, methods_off, get_mstr, modules, dump_func_details
from annotate_sorting_usym import dump_annotated

# 1. Dump GameInteropSubsystem methods in GameAssembly.dll
_, m_cnt_mod, m_ptrs_va = modules["FM.GamePlugin.dll"]
ptrs_off = va_to_off(m_ptrs_va)
tu = struct.unpack_from("<22i", meta, types_off + 13922 * 88)
m_start = tu[9]
m_cnt = tu[16] & 0xFFFF
for mi in range(m_start, m_start + m_cnt):
    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
    mname = get_mstr(mu[0])
    rid = (mu[6] & 0xFFFFFF) - 1
    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
    rva = va - image_base if va else 0
    print(f"GameInteropSubsystem.{mname}: RVA=0x{rva:08x}")
    if mname in ("OpenChannel", "UpdateChannelData", "AddData", "SetData"):
        dump_func_details(f"GameInteropSubsystem.{mname}", rva)
        dump_annotated(f"GameInteropSubsystem.{mname}", rva)

# 2. Inspect game_plugin.dll
gp_path = root / "fm_Data/Plugins/x86_64/game_plugin.dll"
gp = gp_path.read_bytes()

e_lfanew = struct.unpack_from("<I", gp, 0x3C)[0]
num_sec = struct.unpack_from("<H", gp, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", gp, e_lfanew + 20)[0]
gp_base = struct.unpack_from("<Q", gp, e_lfanew + 24 + 24)[0]
exc_rva, exc_sz = struct.unpack_from("<II", gp, e_lfanew + 24 + 112 + 3 * 8)
sec_off = e_lfanew + 24 + opt_size
gp_secs = []
for i in range(num_sec):
    s = gp[sec_off + i * 40 : sec_off + (i + 1) * 40]
    name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
    gp_secs.append((name, vaddr, vsize, raddr, rsize))
print("game_plugin.dll sections:", gp_secs)

def gp_off_to_rva(off):
    for _, vaddr, _, raddr, rsize in gp_secs:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return 0

def gp_rva_to_off(rva):
    for _, vaddr, vsize, raddr, rsize in gp_secs:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

gp_funcs = []
if exc_rva and exc_sz:
    exc_off = gp_rva_to_off(exc_rva)
    for i in range(0, exc_sz, 12):
        b_rva, e_rva, u_rva = struct.unpack_from("<III", gp, exc_off + i)
        if b_rva:
            gp_funcs.append((b_rva, e_rva))
gp_func_starts = [f[0] for f in gp_funcs]

for label, pat in [("22js (LE)", b"22js"), ("22js (BE)", b"sj22"), ("J1Ct (LE)", b"J1Ct"), ("J1Ct (BE)", b"tC1J"), ("wy4A (LE)", b"wy4A"), ("wy4A (BE)", b"A4yw"), ("plyr (LE)", b"rylp"), ("plyr (BE)", b"plyr"), ("axMd (LE)", b"axMd"), ("axMd (BE)", b"dMxa")]:
    pos = 0
    print(f"\n=== game_plugin.dll occurrences of {label} ===")
    while True:
        idx = gp.find(pat, pos)
        if idx == -1:
            break
        rva = gp_off_to_rva(idx)
        bi = bisect.bisect_right(gp_func_starts, rva) - 1
        fn_info = f"func 0x{gp_funcs[bi][0]:08x}..0x{gp_funcs[bi][1]:08x}" if bi >= 0 and gp_funcs[bi][0] <= rva < gp_funcs[bi][1] else "data/unknown"
        ctx = gp[max(0, idx-16):idx+32]
        print(f"  off=0x{idx:08x} RVA=0x{rva:08x} ({fn_info}): {ctx.hex(' ')}")
        pos = idx + 1
