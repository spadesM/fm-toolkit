import struct
from dump_table_factory_methods import dump_clean, pe, image_base
from check_header_all_methods import off_to_va

def find_callers(target_rva, name):
    print(f"\n=== Callers of {name} (0x{target_rva:08x}) ===")
    for op in (0xE8, 0xE9):
        pos = 0
        while True:
            idx = pe.find(bytes([op]), pos)
            if idx < 0 or idx + 5 > len(pe):
                break
            disp = struct.unpack_from("<i", pe, idx + 1)[0]
            va = off_to_va(idx)
            if va:
                caller_rva = va - image_base
                if caller_rva + 5 + disp == target_rva:
                    print(f"  {'CALL' if op == 0xE8 else 'JMP'} at RVA 0x{caller_rva:08x}")
            pos = idx + 1

find_callers(0x015a4260, "StreamedListView.ApplySorting")
find_callers(0x00abdcc0, "StreamedListView.SetSortColumn_0x00abdcc0")
find_callers(0x015efce0, "StreamedTable.SetSorting")
find_callers(0x015ec910, "StreamedTable.OnHeaderClicked")

dump_clean("Func_0x00abdcc0_FULL", 0x00abdcc0, 750)
dump_clean("Func_0x015a9c80_FULL", 0x015a9c80, 700)
