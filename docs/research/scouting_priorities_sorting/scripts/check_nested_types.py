import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_sorting_details import dump_fast, pe, meta, hdr, str_off, str_sz, methods_off, methods_sz, types_off, types_sz, get_mstr, image_base, va_to_off

# Find CodeRegistration to get method pointers if needed, or scan types 5960..5990
for ti in range(5960, 5995):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    mstart = tu[9]
    mcount = tu[16] & 0xFFFF
    print(f"Type {ti}: {tns}.{tname} (methods {mstart}..{mstart+mcount})")
    for mi in range(mstart, mstart + mcount):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        print(f"  Method {mi}: {mname}")

dump_fast("Method_015f2ea0_full", 0x015f2ea0, 0x015f33f0)
dump_fast("After_Deserialize_015f4500_015f5200", 0x015f4500, 0x015f5200)
