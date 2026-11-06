import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, meta, image_base, off_to_va, va_to_off, dump_func_details

hashes = [
    0x72692047, 0x67393649, 0x736a3232, 0x73735043,
    0x706c7972, 0x644d7861, 0x63594545, 0x75446333, 0x71754c76, 0x73714e20, 0x6e475773
]

start_off = va_to_off(image_base + 0x003e4f30)
end_off = va_to_off(image_base + 0x004c5d06)
chunk = pe[start_off:end_off]

for h in hashes:
    pat = b"\xb9" + struct.pack("<I", h)
    idx = chunk.find(pat)
    if idx != -1:
        rva = 0x003e4f30 + idx
        dump_func_details(f"Hash 0x{h:08x} ({struct.pack('<I', h)})", rva - 0x10, 0x90)
