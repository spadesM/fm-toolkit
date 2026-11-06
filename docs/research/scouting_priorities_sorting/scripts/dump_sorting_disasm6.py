import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm6.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name
)
from dump_headers_fast import dump_fast

hdr = struct.unpack_from("<64I", meta, 0)
real_fields_off = hdr[24]
field_offsets_va = 0x182d12000
field_offsets_off = va_to_off(field_offsets_va)

print("=== 1. Dump Bindings and nested types in SI.Bindable.dll ===")
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if ti in range(5680, 5740) or "Binding" in tname or "Scope" in tname or "Channel" in tname or "Node" in tname:
                f_start, f_cnt = tu[8], tu[17] & 0xFFFF
                m_start, m_cnt = tu[9], tu[16] & 0xFFFF
                f_ptr = struct.unpack_from("<Q", pe, field_offsets_off + ti * 8)[0]
                f_off_arr = va_to_off(f_ptr) if f_ptr else 0
                print(f"\n--- Type {ti}: {tname} (fields={f_cnt}, methods={m_cnt}) ---")
                for fi in range(f_start, f_start + f_cnt):
                    fu = struct.unpack_from("<3i", meta, real_fields_off + fi * 12)
                    foff = struct.unpack_from("<I", pe, f_off_arr + (fi - f_start) * 4)[0] if f_off_arr > 0 else -1
                    print(f"  Field {fi - f_start:2d} (+0x{foff:02x}): {get_mstr(fu[0])}")

print("\n=== 2. Disassemble Bindings helper methods ===")
for name, rva in [
    ("Bindings.AddCallback_014d0a20 (Bindings.cs:736)", 0x014d0a20),
    ("Bindings.OpenScope_014d0ca0 (Bindings.cs:632)", 0x014d0ca0),
    ("Bindings.GetRecord_014d1c30 (Bindings.cs:557)", 0x014d1c30),
    ("Bindings.Set_1919 (0x014c5740)", 0x014c5740),
]:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dump_fast(name, rva, end_rva)

print("\n=== 3. Find ScoutPriorities in TeamReference / FM.UI.dll ===")
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "FM.UI.dll":
        t_start, t_cnt = iu[2], iu[3]
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if any(k in tname.lower() for k in ("scout", "priorit", "recruitment", "shortlist", "search")):
                print(f"  Type {ti}: {tname}")

out_file.close()
print("Done!", file=sys.__stdout__)
