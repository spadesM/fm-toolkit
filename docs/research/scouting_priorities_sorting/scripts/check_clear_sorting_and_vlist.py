import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
import check_deep_sorting as cds

pe = dhf.pe
def off_to_rva(off):
    for _, vaddr, vsize, raddr, rsize in dhf.sections:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return -1

# Find callers of 0x015ef750 and 0x015a99d0
for target_name, target in [("StreamedTable_2096 (0x015ef750)", 0x015ef750), ("StreamedListView.SetNoSorting (0x015a99d0)", 0x015a99d0)]:
    print(f"=== Callers of {target_name} ===")
    start_off = dhf.va_to_off(dhf.image_base + 0x01400000)
    end_off = dhf.va_to_off(dhf.image_base + 0x01800000)
    for pos in range(start_off, end_off):
        if pe[pos] in (0xE8, 0xE9):
            rel = struct.unpack_from('<i', pe, pos + 1)[0]
            rva = off_to_rva(pos)
            if rva + 5 + rel == target:
                ud = dhf.get_usym_dict(rva - 0x10, 0x20)
                print(f"  0x{rva:08x} ({ud})")

# Dump 0x015ef890..0x015efc40 and VirtualisedList methods (0x016a7400..0x016ac000)
dhf.dump_fast("StreamedTable_0x015ef890..0x015efc40", 0x015ef890, 0x015efc40)
dhf.dump_fast("VirtualisedList_SetSortedIndices_0x016abc90", 0x016ab800, 0x016ac000)
dhf.dump_fast("VirtualisedList_Bind_0x016a7400..0x016a9600", 0x016a7400, 0x016a9600)
