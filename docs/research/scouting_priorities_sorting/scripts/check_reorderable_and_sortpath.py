import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf

pe = dhf.pe
def off_to_rva(off):
    for _, vaddr, vsize, raddr, rsize in dhf.sections:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return -1

# 1. Find all CALL/JMP to 0x015acdf0 (StreamedListView.get_Reorderable)
target = 0x015acdf0
print("=== Callers of 0x015acdf0 (get_Reorderable) ===")
start_off = dhf.va_to_off(dhf.image_base + 0x00100000)
end_off = dhf.va_to_off(dhf.image_base + 0x02200000)
for pos in range(start_off, end_off):
    b = pe[pos]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from('<i', pe, pos + 1)[0]
        rva = off_to_rva(pos)
        if rva + 5 + rel == target:
            ud = dhf.get_usym_dict(rva - 0x20, 0x40)
            print(f"  0x{rva:08x} ({ud})")

# 2. Find all references to offset 0x4c1 (c1 04 00 00) in code range 0x01500000..0x01700000
print("\n=== References to +0x4c1 in 0x01500000..0x01700000 ===")
pat = b'\xc1\x04\x00\x00'
s_off = dhf.va_to_off(dhf.image_base + 0x01500000)
e_off = dhf.va_to_off(dhf.image_base + 0x01700000)
idx = s_off
while True:
    idx = pe.find(pat, idx, e_off)
    if idx == -1:
        break
    rva = off_to_rva(idx)
    ud = dhf.get_usym_dict(rva - 0x20, 0x40)
    print(f"  0x{rva:08x} ({ud}): {pe[idx-4:idx+8].hex(' ')}")
    idx += 1

# 3. Dump StreamedListView.SubscribeSortPath (0x015a4850) and EvaluateItemSort (0x015aa320)
dhf.dump_fast("StreamedListView.SubscribeSortPath_015a4850", 0x015a4850, 0x015a4d00)
dhf.dump_fast("StreamedListView.EvaluateItemSort_015aa320", 0x015aa320, 0x015aa650)
