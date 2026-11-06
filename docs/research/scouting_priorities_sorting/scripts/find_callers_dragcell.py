import struct, sys, bisect, re
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out = open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\callers_dragcell.txt", "w", encoding="utf-8")
sys.stdout = out
from check_deep_sorting import pe, va_to_off, image_base, rva_to_end, rva_to_method_name, dump_func_details, sections
sorted_rvas = sorted(rva_to_method_name.keys())
def owner(rva):
    i = bisect.bisect_right(sorted_rvas, rva) - 1
    s = sorted_rvas[i]
    return s, rva_to_method_name[s]

text = [s for s in sections if s[0] == ".text"][0]
_, vaddr, vsize, raddr, rsize = text
code = pe[raddr:raddr+rsize]
targets = {0x14dad90: "VirtualisedList.get_Reorderable", 0x15f2230: "StreamedTable.get_IsDragCellActive", 0x15f2190: "StreamedTable.get_DisableSorting"}
for i in range(len(code) - 5):
    if code[i] in (0xE8, 0xE9):
        disp = struct.unpack_from("<i", code, i + 1)[0]
        t = vaddr + i + 5 + disp
        if t in targets:
            rva = vaddr + i
            s, n = owner(rva)
            print(f"{targets[t]} <- {hex(rva)} in {hex(s)} {n[:3]}")
dump_func_details("StreamedTable.get_IsDragCellActive", 0x15f2230)
out.close()
