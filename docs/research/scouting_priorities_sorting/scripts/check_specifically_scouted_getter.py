import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end, rva_to_method_name, dump_func_details
)

# 1. Search for b8 4b 63 46 66 c3 (mov eax, 0x6646634b; ret)
pat = b"\xb8\x4b\x63\x46\x66\xc3"
for sname, rva_s, vsz, raw_ptr, rawsz in sections:
    idx = pe.find(pat, raw_ptr, raw_ptr + rawsz)
    if idx != -1:
        hit_rva = rva_s + (idx - raw_ptr)
        print(f"Found mov eax, 0x6646634b; ret at RVA 0x{hit_rva:08x}: {rva_to_method_name.get(hit_rva)}")

# 2. Look at PropertyRegistration.Initialise around 0x004683e0 (where 0x67393649 is registered!)
# Wait: let's see how PropertyRegistration.Initialise registers a property!
# Let's dump 0x00468280..0x00468500 and check what calls are made!
off = va_to_off(image_base + 0x00468280)
chunk = pe[off:off+0x280]
# Find 49 36 39 67 (0x67393649) in chunk
idx = chunk.find(b"\x49\x36\x39\x67")
print(f"0x67393649 at offset +0x{idx:x} (RVA 0x{0x00468280 + idx:08x})")
# Let's inspect all RIP-relative loads and CALLs around 0x00468280..0x00468500
for p in range(0, len(chunk) - 7):
    rva = 0x00468280 + p
    if chunk[p] == 0xe8:
        rel = struct.unpack_from("<i", chunk, p + 1)[0]
        target = (rva + 5 + rel) & 0xFFFFFFFF
        print(f"  0x{rva:08x}: CALL 0x{target:08x} -> {rva_to_method_name.get(target)}")
    elif chunk[p:p+3] in (b"\x48\x8b\x05", b"\x4c\x8b\x05", b"\x48\x8b\x0d", b"\x4c\x8b\x0d", b"\x48\x8b\x15"):
        rel = struct.unpack_from("<i", chunk, p + 3)[0]
        target = (rva + 7 + rel) & 0xFFFFFFFF
        print(f"  0x{rva:08x}: MOV reg, [0x{target:08x}]")
    elif chunk[p] == 0xb9:
        imm = struct.unpack_from("<I", chunk, p + 1)[0]
        fc = struct.pack("<I", imm).decode("ascii", errors="replace")
        print(f"  0x{rva:08x}: MOV ecx, 0x{imm:08x} ({fc!r})")
