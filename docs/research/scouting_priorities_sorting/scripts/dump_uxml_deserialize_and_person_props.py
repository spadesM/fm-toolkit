import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\uxml_deserialize_and_person_props.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

method_to_rvas = {}
for rva, nms in rva_to_method_name.items():
    for nm in nms:
        method_to_rvas.setdefault(nm, []).append(rva)

print("=== 1. Find UxmlSerializedData.Deserialize near 0x15a0000 - 0x1630000 ===")
for rva, nms in sorted(rva_to_method_name.items()):
    if 0x15a0000 <= rva <= 0x1630000:
        if any("Deserialize" in nm for nm in nms):
            sz = min(rva_to_end.get(rva, rva + 2000) - rva, 3000)
            dump_func_details(f"{nms} @ {hex(rva)}", rva, sz)

print("\n=== 2. Find all Reference types with Player or Person or Scout in name ===")
hdr = struct.unpack_from("<80I", meta, 0)
types_sz = hdr[41]
num_types = types_sz // 88

for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if "Reference" in tname and any(w in tname for w in ("Player", "Person", "Scout", "Report", "Division", "Team", "TransferValue")):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (methods={m_cnt})")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rvas = method_to_rvas.get(f"{tname}.{mname}", [])
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in rvas]}")

print("\n=== 3. Search for SpecificallyScoutedPerson property IDs in GameAssembly.dll ===")
# Property IDs of SpecificallyScoutedPersonReference:
# 0x706c7972 ('plyr' -> Player)
# 0x644d7861 ('axMd' -> ?)
# 0x63594545 ('EEYc' -> Scout)
# 0x75446333 ('3cDu' -> ?)
# 0x71754c76 ('vLuq' -> ?)
# 0x73714e20 (' Nqs' -> ?)
# 0x6e475773 ('sWGn' -> ?)
for pid_val, label in [
    (0x7443314a, "SpecificallyScoutedPerson type ID"),
    (0x644d7861, "prop 0x644d7861"),
    (0x63594545, "prop 0x63594545 (Scout?)"),
    (0x75446333, "prop 0x75446333"),
    (0x71754c76, "prop 0x71754c76"),
    (0x73714e20, "prop 0x73714e20"),
    (0x6e475773, "prop 0x6e475773"),
]:
    pat = struct.pack("<I", pid_val)
    idx = 0
    hits = []
    while True:
        idx = pe.find(pat, idx)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            # find enclosing method
            # binary search or backward scan
            for mrva in range(rva, max(0, rva - 4096), -1):
                if mrva in rva_to_method_name:
                    hits.append((hex(rva), hex(mrva), rva_to_method_name[mrva]))
                    break
            else:
                hits.append((hex(rva), None, None))
        idx += 1
    print(f"\nHits for {label} ({hex(pid_val)}): {len(hits)}")
    for h in hits[:30]:
        print(f"  {h}")

out_file.close()
