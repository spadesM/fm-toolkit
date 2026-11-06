import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from fast_usym_lookup import pe, meta, hdr, str_off, methods_off, types_off, get_mstr, image_base, va_to_off, lookup_usym, sections

def off_to_va(off):
    for _, vaddr, _, raddr, rsize in sections:
        if raddr <= off < raddr + rsize:
            return image_base + vaddr + (off - raddr)
    return 0

# Find SI.Bindable.dll module
sb_str_off = pe.find(b"\x00SI.Bindable.dll\x00") + 1
sb_mod_off = pe.find(struct.pack("<Q", off_to_va(sb_str_off)))
name_va, m_cnt, m_ptrs_va = struct.unpack_from("<QQQ", pe, sb_mod_off)
ptrs_off = va_to_off(m_ptrs_va)

def get_method_rva(mi):
    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
    mname = get_mstr(mu[0])
    rid = (mu[6] & 0xFFFFFF) - 1
    va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
    return mname, (va - image_base if va else 0)

print("=== StreamedListView methods ===")
for mi in range(47153, 47338):
    mname, rva = get_method_rva(mi)
    if any(k in mname for k in ("Sort", "Reorder", "State", "Bind", "Header", "Column", "Refresh", "Rebuild", "SetList")):
        print(f"  [{mi}] {mname}: 0x{rva:08x}")

print("\n=== StreamedTable methods ===")
for mi in range(48771, 48948):
    mname, rva = get_method_rva(mi)
    if any(k in mname for k in ("Sort", "Reorder", "Header", "Column", "Bind", "Init", "View", "SetList", "Rebuild", "Refresh")):
        print(f"  [{mi}] {mname}: 0x{rva:08x}")
