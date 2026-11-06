import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26"
GA_PATH = GAME_DIR + r"\GameAssembly.dll"
OUT_PATH = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\disasm_streamed_table_utf8.txt"

import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name
)

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disasm_func(out, name, start_rva, size):
    out.write(f"\n================ {name} (RVA=0x{start_rva:08x}, size=0x{size:x}) ================\n")
    off = va_to_off(image_base + start_rva)
    code = pe[off : off + size]
    for insn in md.disasm(code, start_rva):
        comment = ""
        if insn.mnemonic in ("call", "jmp") and insn.op_str.startswith("0x"):
            try:
                target = int(insn.op_str, 16)
                mname = rva_to_method_name.get(target, "")
                if mname:
                    comment = f" ; -> {mname}"
            except:
                pass
        out.write(f"  0x{insn.address:08x} (+0x{insn.address - start_rva:03x}): {insn.mnemonic:8s} {insn.op_str:35s}{comment}\n")

with open(OUT_PATH, "w", encoding="utf-8") as out:
    # Print all methods in rva_to_method_name around 0x015e0000..0x015f8000
    out.write("=== Methods in 0x015a0000..0x015f8000 ===\n")
    for rva in sorted(rva_to_method_name.keys()):
        if 0x015a0000 <= rva <= 0x015f8000:
            out.write(f"  0x{rva:08x}: {rva_to_method_name[rva]}\n")

    disasm_func(out, "StreamedTable.SetSorting_1", 0x015efc40, 0xa0)
    disasm_func(out, "StreamedTable.SetSorting_2", 0x015efce0, 0x290)
    disasm_func(out, "StreamedTable.Func_0x015eff70", 0x015eff70, 0xd0)
    disasm_func(out, "StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x1f0)
    disasm_func(out, "StreamedTable.Func_0x015f0230", 0x015f0230, 0x310)
    disasm_func(out, "StreamedTable.Func_0x015f0540", 0x015f0540, 0x400)
    disasm_func(out, "StreamedTable.UpdateSortColumn_and_Persisted", 0x015f1290, 0x400)
    disasm_func(out, "StreamedTable.EntryForColumn_and_neighbors", 0x015e9000, 0x1000)
    disasm_func(out, "StreamedListView.SetSortingBinding", 0x015a9a80, 0x200)
    disasm_func(out, "Bindings.GetProperties", 0x014c1a60, 0x200)
    disasm_func(out, "Func_0x00e030e0", 0x00e030e0, 0x200)
    disasm_func(out, "Func_0x00a5bbf0", 0x00a5bbf0, 0x200)
