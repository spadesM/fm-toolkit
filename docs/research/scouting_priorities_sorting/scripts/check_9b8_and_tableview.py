import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, hdr, va_to_off, off_to_va, image_base, root,
    rva_to_method_name, dump_func_details, get_mstr,
    types_off, types_sz, fields_off, fields_sz, methods_off, methods_sz, images_off, images_sz, modules
)
from dump_headers_fast import dump_fast

print("=== 1. StreamedTable.UxmlSerializedData.Deserialize (0x015f36b0..0x015f4170) ===")
dump_fast("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0, 0x015f4170)

print("\n=== 2. Search for +0x9b8 (b8 09 00 00) in StreamedTable (0x015de000..0x015f6000) ===")
start_off = va_to_off(image_base + 0x015de000)
end_off = va_to_off(image_base + 0x015f6000)
pos = start_off
while True:
    idx = pe.find(b"\xb8\x09\x00\x00", pos, end_off)
    if idx == -1:
        break
    rva = off_to_va(idx) - image_base
    print(f"  Found +0x9b8 at RVA 0x{rva:08x}")
    dump_fast(f"ref_9b8_{rva:08x}", rva - 0x20, rva + 0x30)
    pos = idx + 1

print("\n=== 3. Check callers of set_DisableSorting (0x015f2420) across entire GameAssembly.dll ===")
target_rva = 0x015f2420
text_sec = [s for s in sections if s[0] == ".text"][0]
text_start = text_sec[3]
text_end = text_start + text_sec[4]

for opcode in (b"\xe8", b"\xe9"):
    pos = text_start
    while True:
        idx = pe.find(opcode, pos, text_end)
        if idx == -1:
            break
        rel = struct.unpack_from("<i", pe, idx + 1)[0]
        call_rva = (off_to_va(idx) - image_base)
        if call_rva + 5 + rel == target_rva:
            print(f"  Call to set_DisableSorting at RVA 0x{call_rva:08x}")
            dump_fast(f"caller_set_DisableSorting_{call_rva:08x}", call_rva - 0x30, call_rva + 0x30)
        pos = idx + 1

print("\n=== 4. Check StreamedTableView and TableFactory type definitions and fields ===")
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    t_start, t_cnt = iu[2], iu[3]
    _, m_cnt_mod, m_ptrs_va = modules.get(iname, (0, 0, 0))
    ptrs_off = va_to_off(m_ptrs_va) if m_ptrs_va else -1
    for ti in range(t_start, t_start + t_cnt):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        tns = get_mstr(tu[1])
        if any(k in tname for k in ("StreamedTableView", "SpecificallyScoutedPersonTableFactory", "StreamedTableFactory")):
            f_start = tu[8]
            f_cnt = tu[17] & 0xFFFF
            m_start = tu[9]
            m_cnt = tu[16] & 0xFFFF
            print(f"\nType[{ti}] {tns}.{tname} (fields={f_cnt}, methods={m_cnt})")
            for fi in range(f_start, f_start + f_cnt):
                fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
                print(f"  Field[{fi - f_start}] {get_mstr(fu[0])}")
            for mi in range(m_start, m_start + m_cnt):
                mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                mname = get_mstr(mu[0])
                rid = (mu[6] & 0xFFFFFF) - 1
                va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0] if (ptrs_off > 0 and 0 <= rid < m_cnt_mod) else 0
                rva = va - image_base if va else 0
                print(f"  Method {mname} @ 0x{rva:08x}")
