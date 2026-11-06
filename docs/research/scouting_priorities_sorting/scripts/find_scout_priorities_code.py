import struct, sys

out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\scout_priorities_code_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

print("=== 1. Types 900..925 in global-metadata.dat ===")
for ti in range(900, 925):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"Type {ti}: {tns}.{tname} (methods={m_cnt})")
    if ti in (908, 911, 912):
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            found_rvas = [r for r, nms in rva_to_method_name.items() if f"{tname}.{mname}" in nms]
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in found_rvas]}")

print("\n=== 2. Search GameAssembly.dll for SpecificallyScoutedPerson property hashes ===")
for prop_hash, label in [
    (0x75446333, "3cDu (prop 4 of SpecificallyScoutedPerson)"),
    (0x71754c76, "vLuq (prop 5 of SpecificallyScoutedPerson)"),
    (0x73714e20, " Nqs (prop 6 of SpecificallyScoutedPerson)"),
    (0x6e475773, "sWGn (prop 7 of SpecificallyScoutedPerson)"),
    (0x63594545, "EEYc (Scout prop)"),
    (0x644d7861, "axMd (Priority prop)"),
]:
    pat = struct.pack("<I", prop_hash)
    pos = 0
    print(f"\n--- Searching for 0x{prop_hash:08x} ({label}) ---")
    while True:
        idx = pe.find(pat, pos)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va > 0:
            rva = va - image_base
            fn_rva = max((k for k in rva_to_end if k <= rva and rva < rva_to_end[k]), default=0)
            print(f"  Found at RVA=0x{rva:08x} in {rva_to_method_name.get(fn_rva)} (0x{fn_rva:08x})")
            if fn_rva > 0 and not (0x00696ef0 <= fn_rva <= 0x00697c00):
                sz = min(rva_to_end.get(fn_rva, fn_rva + 800) - fn_rva, 1500)
                dump_func_details(f"Handler {rva_to_method_name.get(fn_rva)}", fn_rva, sz)
        pos = idx + 1

print("\n=== 3. Search all TypeDefinitions for 'Scout' or 'Priorit' or 'Recruitment' ===")
hdr = struct.unpack("<64I", meta[:256])
num_types = hdr[41] // 88
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if any(k in tname.lower() for k in ("scoutpriorit", "specificallyscouted", "scoutingpriorit")):
        print(f"Match Type {ti}: {tns}.{tname}")

out_file.close()
