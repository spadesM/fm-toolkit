import struct, sys, bisect

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\dump_468_and_scout_priorities.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

sorted_rvas = sorted(rva_to_method_name.keys())

print("=== 1. Check 0x468bb7 .. 0x46cb53 in GameAssembly.dll ===")
for target_rva in [0x468bb7, 0x468c2d, 0x468ca3, 0x468d8f, 0x46b097, 0x46cb53]:
    idx = bisect.bisect_right(sorted_rvas, target_rva) - 1
    if idx >= 0:
        s_rva = sorted_rvas[idx]
        e_rva = rva_to_end.get(s_rva, 0)
        print(f"Target {hex(target_rva)}: prev symbol @ {hex(s_rva)} (end={hex(e_rva)}) -> {rva_to_method_name[s_rva]}")
    if idx + 1 < len(sorted_rvas):
        n_rva = sorted_rvas[idx + 1]
        print(f"  next symbol @ {hex(n_rva)} -> {rva_to_method_name[n_rva]}")

# Let's find the function start before 0x468bb7 by looking for int3 (0xcc) padding or prologue!
off_468 = va_to_off(image_base + 0x468bb7)
for back in range(0, 0x10000, 16):
    r = 0x468bb0 - back
    o = va_to_off(image_base + r)
    if pe[o-2:o] == b"\xcc\xcc":
        print(f"Found function start candidate @ {hex(r)} (distance={hex(0x468bb7 - r)})")
        if 0x468bb7 - r > 0x100:
            break

dump_func_details("Producer @ 0x468b00..0x468f00", 0x468b00, 0x400)
dump_func_details("Producer @ 0x467f00..0x468b00", 0x467f00, 0xc00)
dump_func_details("Producer @ 0x46b000..0x46b200", 0x46b000, 0x200)
dump_func_details("Producer @ 0x46ca80..0x46cc80", 0x46ca80, 0x200)

print("\n=== 2. Dump ScoutPlayerPrioritiesReference (Type 860) ===")
for name, rva, sz in [
    ("ScoutPlayerPrioritiesReference.get_ID", 0x67d650, 0x30),
    ("ScoutPlayerPrioritiesReference.AcceptsPropertyInternal", 0x67d270, 0x60),
    ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x67d360, 0x1a0),
    ("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x67d500, 0x150),
    ("ScoutPlayerPrioritiesReference.DerivesFromInternal", 0x67d2b0, 0x20),
    ("ScoutPlayerPrioritiesReference.DerivesFrom", 0x67d2c0, 0x20),
]:
    dump_func_details(name, rva, sz)

print("\n=== 3. Dump ScoutTeamPrioritiesReference (Type 861) ===")
# Let's check what methods Type 861 has
tu860 = struct.unpack_from("<22i", meta, types_off + 860 * 88)
tu861 = struct.unpack_from("<22i", meta, types_off + 861 * 88)
for ti, tu in [(860, tu860), (861, tu861)]:
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"Type {ti}: {tname}")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        print(f"  Method {mi - m_start}: {mname}")

# Dump 0x67d660 .. 0x67dc00 (which is likely ScoutTeamPrioritiesReference!)
for rva in sorted_rvas:
    if 0x67d200 <= rva <= 0x67dc50:
        sz = rva_to_end.get(rva, rva + 0x100) - rva
        dump_func_details(f"{rva_to_method_name[rva]} @ {hex(rva)}", rva, sz)

print("\n=== 4. Search for ScoutPlayerPrioritiesReference ID & prop IDs in GameAssembly.dll ===")
off_id = va_to_off(image_base + 0x67d650)
print("Bytes at 0x67d650:", pe[off_id:off_id+16].hex(" "))
if pe[off_id] == 0xb8:
    spp_id = struct.unpack_from("<I", pe, off_id + 1)[0]
    print(f"ScoutPlayerPrioritiesReference ID = {hex(spp_id)} ({struct.pack('<I', spp_id)})")
    pat = struct.pack("<I", spp_id)
    idx = 0
    while True:
        idx = pe.find(pat, idx)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            s_idx = bisect.bisect_right(sorted_rvas, rva) - 1
            s_rva = sorted_rvas[s_idx] if s_idx >= 0 else 0
            print(f"  Hit @ {hex(rva)} in {hex(s_rva)} ({rva_to_method_name.get(s_rva)})")
        idx += 1

print("\n=== 5. Search for offset 0x780, 0x788, 0x838, 0x840 in 0x15a0000..0x16c0000 ===")
s_off = va_to_off(image_base + 0x15a0000)
e_off = va_to_off(image_base + 0x16c0000)
for pat_name, pat in [("0x780", b"\x80\x07\x00\x00"), ("0x788", b"\x88\x07\x00\x00"), ("0x838", b"\x38\x08\x00\x00"), ("0x840", b"\x40\x08\x00\x00")]:
    pos = s_off
    hits = []
    while True:
        idx = pe.find(pat, pos, e_off)
        if idx == -1:
            break
        va = off_to_va(idx)
        if va:
            rva = va - image_base
            s_idx = bisect.bisect_right(sorted_rvas, rva) - 1
            s_rva = sorted_rvas[s_idx] if s_idx >= 0 else 0
            hits.append((hex(rva), hex(s_rva), rva_to_method_name.get(s_rva)))
        pos = idx + 1
    print(f"Hits for {pat_name}: {len(hits)}")
    for h in hits:
        print(f"  {h}")

out_file.close()
