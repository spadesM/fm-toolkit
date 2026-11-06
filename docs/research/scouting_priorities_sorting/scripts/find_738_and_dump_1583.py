import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

pe = dhf.pe
s_off = dhf.va_to_off(dhf.image_base + 0x015a0000)
e_off = dhf.va_to_off(dhf.image_base + 0x01600000)

print("=== References to +0x738 in StreamedListView / StreamedTable ===")
pat = b"\x38\x07\x00\x00"
idx = s_off
while True:
    idx = pe.find(pat, idx, e_off)
    if idx == -1:
        break
    rva = 0x015a0000 + (idx - s_off)
    ud = dhf.get_usym_dict(rva - 0x10, 0x20)
    print(f"  0x{rva:08x} ({ud}): {pe[idx-4:idx+8].hex(' ')}")
    idx += 1

dhf.dump_fast("StreamedListView_1583", 0x015a9400, 0x015a99d0)
