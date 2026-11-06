from capstone import *
from check_deep_sorting import pe, va_to_off, rva_to_names

md = Cs(CS_ARCH_X86, CS_MODE_64)

def cs_dump(name, rva, sz):
    print(f"\n================ {name} (RVA=0x{rva:08x}, size={sz}) ================")
    off = va_to_off(rva)
    code = pe[off : off + sz]
    for i in md.disasm(code, rva):
        op_str = i.op_str
        note = ""
        if i.mnemonic in ("call", "jmp") and op_str.startswith("0x"):
            try:
                target = int(op_str, 16)
                if target in rva_to_names:
                    note = f"  ; -> {', '.join(rva_to_names[target][:3])}"
            except:
                pass
        print(f"  +0x{i.address - rva:03x} (0x{i.address:08x}): {i.mnemonic:8s} {op_str}{note}")

cs_dump("StreamedTable.MakeColumnHeader", 0x015eac30, 973)
cs_dump("StreamedTable.OnHeaderClicked", 0x015ec910, 600)
cs_dump("Header..ctor", 0x015dfab0, 400)
cs_dump("Header.Bind", 0x015df4f0, 300)
