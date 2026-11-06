import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import pe, meta, hdr, image_base, va_to_off, get_usym_dict, dump_fast

def rva_to_off(rva):
    return va_to_off(image_base + rva)

print("=== 1. Search for +0x5c1 (c1 05 00 00) and +0x9b8 (b8 09 00 00) in SI.Bindable (0x014b0000..0x016c0000) ===")
start_off = rva_to_off(0x014b0000)
end_off = rva_to_off(0x016c0000)

for disp_bytes, label in [
    (b'\xc1\x05\x00\x00', '+0x5c1 (VirtualisedList.m_reorderable)'),
    (b'\xb8\x09\x00\x00', '+0x9b8 (StreamedTable.m_disableSorting)'),
    (b'\x58\x09\x00\x00', '+0x958 (StreamedTable.m_dragCellID)'),
]:
    print(f"\nOccurrences of {label}:")
    pos = start_off
    while True:
        idx = pe.find(disp_bytes, pos, end_off)
        if idx == -1:
            break
        rva = 0x014b0000 + (idx - start_off)
        umap = get_usym_dict(rva - 8, 24)
        uinfo = []
        for k, v in sorted(umap.items()):
            uinfo.extend(v)
        ctx = pe[idx-4:idx+6].hex(' ')
        print(f"  0x{rva:08x}: {ctx} | {uinfo[:3]}")
        pos = idx + 1

for name, s, e in [
    ("StreamedListView.set_Reorderable", 0x015ad4f0, 0x015ad580),
    ("StreamedTable.get_DisableSorting", 0x015f2190, 0x015f21c0),
    ("StreamedTable.set_DisableSorting", 0x015f2420, 0x015f2450),
    ("StreamedTable.get_IsDragCellActive", 0x015f2230, 0x015f2290),
    ("StreamedTable.CanPopulateTable", 0x015e7640, 0x015e7720),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70, 0x015f0040),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x015f0380),
    ("Header..ctor", 0x015dfab0, 0x015dfce0),
    ("Header.Bind", 0x015df4f0, 0x015df7e0),
    ("Header.SetupClickHandler", 0x015df7e0, 0x015dfab0),
    ("<>c__DisplayClass259_0.<MakeColumnHeader>b__0", 0x0160bb80, 0x0160bc00),
    ("SortData.HasReceived", 0x015a4040, 0x015a4260),
]:
    dump_fast(name, s, e)
